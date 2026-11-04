# English term paper

[论文 PDF](main.pdf) · [LaTeX 正文](main.tex) · [LaTeX 源文件包](DSS5202_Group04_LaTeX_Source.zip) · [结果数据](../results/analysis_summary.json)

## 当前稿件

论文比较NUS学生一年参加六次正式活动的新品购买、二手购买和同款租赁。正文采用原始问卷的1、2、3比率映射与全部17份完整回答，报告个人及群体一致性、年度LCA/LCC结果、AHP加权综合评分和交通敏感性分析。

技术路线图按研究范围、并行评价、综合决策和交通敏感性分析分层组织；年度指标与问卷权重分别进入评分模型。文献图式的查阅记录见[技术路线图绘图说明](framework_design_notes.md)。论文共6页（含参考文献），包含3张矢量图、2张外置结果表及正文中的主要输入表。问卷描述统计保存在原始资料中，正文聚焦研究方法与结果。

## 从原始数据重建

在项目根目录执行（Python 3.11+）：

```sh
python -m pip install -r requirements.txt
python -X utf8 -B code/run.py
python -X utf8 -B -m unittest discover -s tests -v
python -X utf8 -B report/generate_assets.py
```

`results/ahp_individual.csv`保存个人权重及CR，`ahp_group.csv`保存群体权重，`rankings.csv`保存基准评分和排名。交通结果位于`transport_scenarios.csv`与`transport_thresholds.csv`；`analysis_summary.json`汇总实际计算值。图表生成器直接读取这些结果。

## 编译与打包

已有表图可独立编译。在`report/`目录执行：

```sh
tectonic main.tex
```

也可使用TeX Live或MiKTeX，连续执行两次：

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

完成PDF检查后，从项目根目录执行：

```sh
python -X utf8 -B report/package_source.py
```

源文件包包含正文、参考文献、实际引用的表图及技术路线图的可编辑SVG，解压后可直接编译。`delivery_manifest.json`记录LaTeX、PDF和源文件包的SHA-256。代码、原始数据和完整结果随GitHub仓库提供；源文件包用于独立排版编译。

## 本轮结果

环境、成本和便利性权重为0.2410、0.4295和0.3295。二手、新品和租赁的综合分为0.8412、0.8281和0.5189。个人CR达标11/17，群体CR为0.005885。租赁相对二手、新品的交通临界值为基准交通负担的约6.87%和10.67%；计算维持同一组AHP权重及评分参考值。

论文基于原始问卷和已归档证据。参数变更后，请重算并同步核对正文中的数值陈述。

已通过14项模型检查、309条交通情景的独立核验和全部6页视觉检查；编译日志中的引用与版面检查通过。详见`validation.json`。

技术路线图另提供[可编辑SVG](figures/framework.svg)和[高分辨率预览](figures/framework.png)。运行`python -X utf8 -B report/draw_framework.py`可单独重建此图。
