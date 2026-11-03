"""One entry: sources -> annual burdens -> AHP -> scores and explanation."""
import csv
import hashlib
import json
import platform
import warnings
from importlib.metadata import version
from model import ROOT, STAGES, evaluate, load_config, rank, values
from ahp import compute

LABEL = {"new": "新品", "used": "二手", "rental": "租赁"}


def write_csv(name, rows):
    with (ROOT / "results" / name).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def table(headers, rows):
    return "\n".join(["|"+"|".join(headers)+"|", "|"+"|".join(["---"]*len(headers))+"|"]
                     + ["|"+"|".join(map(str, row))+"|" for row in rows])


def main():
    cfg = load_config()
    p = values(cfg)
    rows = evaluate(cfg)
    raw, individual, groups, questions = compute(cfg)
    rankings = []
    for g in groups:
        for r in rank(rows, [g[k] for k in ("w_E", "w_C", "w_V")], cfg):
            if r["outside_reference_range"]:
                warnings.warn(f"{r['mode']} exceeds a reference anchor; linear score retained")
            rankings.append(dict(mapping=g["mapping"], subset=g["subset"], **r))
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    for file, data in (("annual_results.csv", rows), ("ahp_individual.csv", individual),
                       ("ahp_group.csv", groups), ("rankings.csv", rankings), ("survey_input.csv", raw)):
        write_csv(file, data)
    main_group = next(g for g in groups if g["mapping"] == cfg["ahp"]["main_mapping"] and g["subset"] == "all_complete")
    main_ranks = [r for r in rankings if r["mapping"] == cfg["ahp"]["main_mapping"] and r["subset"] == "all_complete"]
    pass_group = next(g for g in groups if g["mapping"] == cfg["ahp"]["main_mapping"] and g["subset"] == "cr_pass")
    baseline = table(["方案", "排放 kgCO₂e/年", "支出 SGD/年", "假设主动时间 分钟/年", "排放分", "成本分", "便利分", "综合分", "排名"],
                     [[LABEL[r["mode"]], f"{b['annual_kgco2e']:.7f}", f"{b['annual_spending_sgd']:.2f}",
                       f"{b['annual_minutes']:g}"] + [f"{r[k]:.6f}" for k in ("emissions_score", "cost_score", "convenience_score", "score")] + [r["rank"]]
                      for r in main_ranks for b in rows if b["mode"] == r["mode"]])
    stages = table(["方案", "制造", "分销零售", "处置", "清洗", "交通/配送"],
                   [[LABEL[r["mode"]]] + [f"{r[s+'_kgco2e']:.7f}" for s in STAGES] for r in rows])
    costs = table(["方案", "购衣", "配送", "租金", "护理", "交通", "可退押金（排除成本）"],
                  [[LABEL[r["mode"]]] + [f"{r[k]:.2f}" for k in ("purchase_sgd", "delivery_sgd", "rental_sgd", "care_sgd", "travel_sgd", "refundable_deposit_sgd")] for r in rows])
    ahp_table = table(["映射", "样本", "n", "排放权重", "成本权重", "便利权重", "群体CR"],
                      [[g["mapping"], g["subset"], g["n"]] + [f"{g[k]:.6f}" for k in ("w_E", "w_C", "w_V", "cr")] for g in groups])
    n = p["events"]
    new, used, rental = rows
    cost_order = "、".join(LABEL[r["mode"]] for r in sorted(rows, key=lambda r: r["annual_spending_sgd"]))
    report = f"""# 三种服装获取方案的年度比较

研究对象为原始报价中的 Love, Bonito **Eyka** 同款S码（请求中的Eykq按来源更正）；中等档次为研究定位，未独立测量品质。功能单位：一名学生一年参加{n:g}次正式活动，允许同款复穿。金额为**新加坡元 SGD**，依据冻结报价显式S$/SGD字段及页面摘录；本轮未联网刷新价格，不保证现时库存和成交条件。

## 自动计算结果

{baseline}

CSV保留计算精度，仅展示时舍入。成本是学生年度支出，购买一次支付完整购衣价，不按寿命分摊价格。

## LCA来源贡献（kgCO₂e/年）

{stages}

制造、分销及处置均按{n:g}/{p['lifetime_wears']:g}分摊；不将二手制造置零，也不改用剩余寿命分母。二手此前穿{p['used_prior_wears']:g}次仅检查：此前+本年={p['used_prior_wears']+n:g}≤总寿命{p['lifetime_wears']:g}。参考重量{p['reference_mass']} kg不额外乘算。

购买清洗{new['cleaning_count']:g}次（初洗+穿后洗），配送{p['delivery_one_way_km']:g}公里×{p['delivery_legs']:g}腿/{p['delivery_batch']:g}件={new['allocated_delivery_vehicle_km']:g}车公里/件。租赁归还后清洗{rental['cleaning_count']:g}次，交通{n:g}×{p['rental_legs']:g}×{p['one_way_km']:g}={rental['passenger_km']:g}人公里，采用轨道代理，不叠加购买配送。

租赁比新品高{rental['annual_kgco2e']-new['annual_kgco2e']:.7f}，其中交通/配送差为{rental['transport_kgco2e']-new['transport_kgco2e']:+.7f}，清洗差为{rental['cleaning_kgco2e']-new['cleaning_kgco2e']:+.7f}。差异主要来自取还交通。新品与二手相同由统一分摊及护理设定导致，不代表所有研究均相同。

制造{p['manufacturing']}、分销{p['distribution']}和毛处置{p['disposal']}来自Sandin图形数字化后取舍的每件代理值，不是作者精确表值。清洗{p['cleaning']}为意大利家庭水洗、烘干及熨烫组合，本地冷水流程和出租方工艺未知。轨道{p['rail']}、货车{p['van']}含直接与能源上游，是英国代理，不是本地实测。详见参数注释与文献证据。

## LCC支出分解（SGD/年）

{costs}

转售与期末残值基准0。正常归还无损坏和迟还，额外平台费基准未计，属于假设。租赁普通护理额外收费0亦为假设，商家未确认全包。购买配送到家不加取衣费。首次可退押金单列，假设全额退还，顺序租赁不累加六次。自动计算支出从低到高为：{cost_order}；结论取决于活动次数和服务流程。

## 问卷AHP

直接读取本地工作簿“原始回答”J:L，{len(raw)}条原始记录中{main_group['n']}份三题完整。R017缺Q8，不填0或中性值；已知比较保留。Q8生成E/C；Q9生成E/V（1为便利优先，反向）；Q10生成C/V（1为成本优先）。矩阵补齐倒数与对角线1。

主映射以代码离3的距离0/1/2映射强度1/3/5，属于研究者转换，不是直接采集的Saaty1—9量表。Q8完整标签见原表；Q9/Q10仅1端点经此前用户确认，2—5标签待核实，暂按对称解释；另报温和映射1/2/3。

个人采用3×3正互反矩阵行几何均值归一化，在此维度与主特征向量等价；代码检查Aw=λw。CI=(λmax−3)/2；CR=CI/RI；RI={p['ri']}取所存Saaty来源p104表，CR≤{p['cr_threshold']}合格。群体逐元素同权几何聚合判断，再求权重，**不是平均个人权重**。截图个人示例不作为群体矩阵。

{ahp_table}

主映射个人CR合格仅{pass_group['n']}/{main_group['n']}，未向受访者复核。主分析保留所有完整回答作探索性结果，不改回答或静默删除；群体低CR不表示个人全一致。合格子样本仅{pass_group['n']}人，不足以推广学生总体。所有样本与映射组合的排名见rankings.csv。

## 标准化、时间和截图核对

年度参考上限为{p['emissions_anchor']*n:g} kgCO₂e、{p['cost_anchor']*n:g} SGD、{p['time_anchor']*n:g}分钟，均为研究设定。各项分=1−年度负担/年度上限；综合分为三项分数乘AHP权重后相加，先算完整精度再展示舍入。超出上限保留负分并警示；负负担、NaN、无穷值报错。

查得原项目时间配置：购买={p['order_minutes']:g}+{new['cleaning_count']:g}×{p['home_care_minutes']:g}={new['annual_minutes']:g}分钟；租赁={n:g}×({p['rental_handling_minutes']:g}+{p['rental_legs']:g}×{p['travel_minutes_per_leg']:g})={rental['annual_minutes']:g}分钟。它们是原项目研究者主动时间假设，并非截图反推后当作实测。排除机器被动运行和出租方劳动，未另设找衣或试穿时间，便利性代理范围有限。

本情景自动重算与请求中截图四位小数分项一致，群体精细权重由原始回答恢复，综合分由完整精度计算。旧代码将线性分截断到[0,1]，现已删除截断；基准未超界，数值不受影响。商品拼写按来源改为Eyka，币种确认为SGD；没有硬编码最终权重或排名。

## 尚待核实

- Q9/Q10全部五档标签，个人高CR原因及受访者理解。
- 主动操作、护理、预约、出行的实测时间；当前购买{new['annual_minutes']:g}/租赁{rental['annual_minutes']:g}分钟为项目假设。
- 租赁实际清洗工艺和普通护理收费、额外平台费用、卫生、六次可租性及购买交货/库存。
- 实物真伪、个体材质/洗标、重量和总寿命；二手此前穿一次未经独立验证，颜色与新品不完全一致。
- 本地交通距离、配送批量、票价和排放因子；现有值为研究情景或跨地区代理。

不含赴活动本身交通、鞋包、事故维修及新增包装，假设复用现有包装。分销因子已有零售边界，未另建店铺/平台/仓库模型。结论限于所选同款与当前假设，不作渠道普遍因果结论。

## 来源与复现

唯一参数：data/parameters.json（数值、单位、来源和假设）；来源索引：data/sources.json；原始报价、服务及因子：data/raw/；文献图表摘录和原时间配置：evidence/。本地原问卷及提案未改、未上传。`python code/run.py`导出结果；`python -m unittest discover -s tests -v`验证。输入哈希、依赖及原始题文见run_manifest.json。
"""
    (out / "report.md").write_text(report, encoding="utf-8")
    inputs = sorted(p for folder in (ROOT / "data", ROOT / "evidence") for p in folder.rglob("*") if p.is_file())
    manifest = {"python": platform.python_version(), "dependencies": {"openpyxl": version("openpyxl")},
                "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                "questions": questions, "main_complete_n": main_group["n"], "main_individual_cr_pass_n": pass_group["n"]}
    (out / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(baseline)


if __name__ == "__main__":
    main()
