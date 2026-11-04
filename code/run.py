"""Reproduce annual burdens, original-survey AHP scores, and transport scenarios."""
import csv
import hashlib
import json
import platform
import warnings
from importlib.metadata import version
from model import (ROOT, STAGES, evaluate, evaluate_transport, load_config, rank,
                   transport_analysis, values)
from ahp import compute

LABEL = {"new": "新品", "used": "二手", "rental": "租赁"}


def write_csv(name, rows):
    with (ROOT / "results" / name).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def table(headers, rows):
    return "\n".join(["|"+"|".join(headers)+"|", "|"+"|".join(["---"]*len(headers))+"|"]
                     + ["|"+"|".join(map(str, row))+"|" for row in rows])


def hashes(paths):
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def main():
    cfg = load_config()
    p = values(cfg)
    rows = evaluate(cfg)
    raw, individual, groups, questions = compute(cfg)
    group = groups[0]
    weights = [group[k] for k in ("w_E", "w_C", "w_V")]
    rankings = [dict(mapping=group["mapping"], subset=group["subset"], **r)
                for r in rank(rows, weights, cfg)]
    for r in rankings:
        if r["outside_reference_range"]:
            warnings.warn(f"{r['mode']} exceeds a reference anchor; linear score retained")
    traffic = transport_analysis(cfg, weights)
    alphas = sorted(set([i / 100 for i in range(101)] +
                        [r["alpha"] for r in traffic["thresholds"]
                         if r["alpha"] is not None and 0 <= r["alpha"] <= 1]))
    scenarios = []
    for alpha in alphas:
        scenario_rows = evaluate_transport(cfg, alpha)
        burdens = {r["mode"]: r for r in scenario_rows}
        for r in rank(scenario_rows, weights, cfg):
            b = burdens[r["mode"]]
            scenarios.append(dict(alpha=alpha, mode=r["mode"],
                **{k: b[k] for k in ("annual_kgco2e", "annual_spending_sgd", "annual_minutes")},
                **{k: r[k] for k in ("emissions_score", "cost_score", "convenience_score", "score", "rank")}))
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    for file, data in (("annual_results.csv", rows), ("ahp_individual.csv", individual),
                       ("ahp_group.csv", groups), ("rankings.csv", rankings), ("survey_input.csv", raw),
                       ("transport_scenarios.csv", scenarios),
                       ("transport_thresholds.csv", traffic["thresholds"])):
        write_csv(file, data)
    pass_n = sum(r["cr_pass"] for r in individual)
    summary = {
        "data_origin": "original_survey", "survey_records": len(raw),
        "complete_comparisons": group["n"], "individual_cr_pass_n": pass_n,
        "mapping": group["mapping"], "mapping_strengths": cfg["ahp"]["mappings"][group["mapping"]],
        "ri": p["ri"], "cr_threshold": p["cr_threshold"],
        "criterion_weights": dict(zip(cfg["ahp"]["criteria"], weights)),
        "group_cr": group["cr"], "group_lambda_max": group["lambda_max"],
        "annual_burdens": rows, "baseline_scores": rankings, "transport": traffic,
    }
    (out / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    baseline = table(["方案", "排放 kgCO₂e/年", "支出 SGD/年", "主动时间 分钟/年", "综合分", "排名"],
        [[LABEL[r["mode"]], f"{b['annual_kgco2e']:.7f}", f"{b['annual_spending_sgd']:.2f}",
          f"{b['annual_minutes']:g}", f"{r['score']:.6f}", r["rank"]]
         for r in rankings for b in rows if b["mode"] == r["mode"]])
    stages = table(["方案", "制造", "分销零售", "处置", "清洗", "交通/配送"],
        [[LABEL[r["mode"]]] + [f"{r[s+'_kgco2e']:.7f}" for s in STAGES] for r in rows])
    crossings = table(["综合评分相等的方案", "交通负担归属比例 α"],
        [["租赁与"+LABEL[r["comparison"].removeprefix("rental_vs_")],
          f"{100*r['alpha']:.4f}%" if r["alpha"] is not None else "交通得分恒定"]
         for r in traffic["thresholds"]])
    coeff = traffic["rental_burden_coefficients"]
    equations = "\n".join(f"- {label} = {coeff[key]['intercept']:.9f} + {coeff[key]['slope']:.9f} × α"
        for key, label in (("annual_kgco2e", "年度排放（kg CO₂e）"),
                           ("annual_spending_sgd", "年度支出（SGD）"),
                           ("annual_minutes", "年度主动时间（分钟）")))
    report = f"""# 三种礼服获取方案的年度比较

功能单位为一名学生一年参加{p['events']:g}次正式活动，比较购买新品、购买二手和逐场租赁同款 Love, Bonito Eyka 礼服。金额为新加坡元。报价、寿命、清洗、配送和主动时间均使用参数表所列来源与情景假设。

## 基准结果

{baseline}

购买价格在购入年度完整计入支出；制造、分销和处置按{p['events']:g}/{p['lifetime_wears']:g}分摊。新品与二手使用相同的清洗、配送和时间设定。租赁包含每次取还的专程交通。

## 排放分解（kg CO₂e/年）

{stages}

## 原始问卷与AHP

原工作簿包含{len(raw)}条记录，其中{group['n']}份具有完整的Q8–Q10回答。Q8生成E/C，Q9反向生成E/V，Q10生成C/V。五档回答距中心位置的距离0、1、2对应比率强度1、2、3；反向偏好采用倒数。矩阵使用行几何均值计算权重，并检查主特征向量残差。

全部{group['n']}份完整矩阵按元素作同权几何聚合。环境、成本和便利性权重分别为{weights[0]:.9f}、{weights[1]:.9f}和{weights[2]:.9f}。RI={p['ri']}、CR≤{p['cr_threshold']}；个人一致性达标{pass_n}/{group['n']}，群体CR={group['cr']:.9f}。这些权重用于探索性综合评价。逐份回答、比率、权重和CR保存在`ahp_individual.csv`。

## 综合评分与交通敏感性

指标得分为1−年度负担/年度参考值，参考值分别为{p['emissions_anchor']*p['events']:g} kg CO₂e、{p['cost_anchor']*p['events']:g} SGD和{p['time_anchor']*p['events']:g}分钟。综合评分使用上述AHP权重加权求和，计算保留完整精度。

α表示计入租赁的取还交通负担占基准交通负担的比例。交通排放、票价和主动出行时间同比例变化；租金、清洗和交接保持固定，权重保持固定。

{equations}
- 租赁综合分 = {traffic['rental_score_intercept']:.9f} {traffic['rental_score_slope']:+.9f} × α

{crossings}

在本组评分参考值和比例变化设定下，租赁在较低临界值以下排名第一，在两个临界值之间排名第二，在较高临界值以上排名第三；临界值处相应方案得分相同。`transport_scenarios.csv`保留0–1区间及精确交叉点的各项负担、得分和排名。

## 来源与复现

参数及来源见`data/parameters.json`、`data/sources.json`和`evidence/`。原始输入位于`data/raw/`；`run_manifest.json`记录输入与计算代码的哈希。`analysis_summary.json`保存本轮分析的完整汇总值。

在项目根目录运行`python -X utf8 -B code/run.py`重建全部结果，运行`python -X utf8 -B -m unittest discover -s tests -v`执行独立公式、来源和边界检查。
"""
    (out / "report.md").write_text(report, encoding="utf-8", newline="\n")
    inputs = [f for folder in (ROOT / "data", ROOT / "evidence") for f in folder.rglob("*") if f.is_file()]
    manifest = {"python": platform.python_version(), "dependencies": {"openpyxl": version("openpyxl")},
                "inputs_sha256": hashes(inputs), "code_sha256": hashes((ROOT / "code").glob("*.py")),
                "questions": questions, "mapping": group["mapping"],
                "main_complete_n": group["n"], "main_individual_cr_pass_n": pass_n,
                "transport_scenario_count": len(alphas)}
    (out / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(baseline)
    print(crossings)


if __name__ == "__main__":
    main()
