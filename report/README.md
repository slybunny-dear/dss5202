# English term paper

[论文 PDF](main.pdf) · [LaTeX 正文](main.tex) · [LaTeX 源文件包](DSS5202_Group04_LaTeX_Source.zip) · [结果数据](../results/analysis_summary.json)

## 当前稿件

论文比较NUS学生一年参加六次正式活动的新品购买、二手购买和同款租赁。正文采用原始问卷的1、2、3比率映射与全部17份完整回答，报告个人及群体一致性、年度LCA/LCC结果、AHP加权综合评分和交通敏感性分析。

技术路线图按研究范围、并行评价、综合决策和交通敏感性分析分层组织，采用彩色模块、虚线分组与可编辑图标；年度指标与问卷权重分别进入评分模型。文献图式的查阅记录及视觉编码见[技术路线图绘图说明](framework_design_notes.md)。LCA产品系统图采用组员提供的原始PDF，明确标注功能单位、内部过程、资源输入、功能输出及系统整体温室气体排放。图件来源、模型对应和历史图件说明见[LCA系统边界图说明](lca_boundary_notes.md)。论文共9页（含参考文献及附录），包含4张矢量图、2张外置结果表及正文中的主要输入表。图表标题居中，正文自然段（包括节标题后的首段及公式后的独立段落）统一首行缩进1.2 em。附录A恢复来源定位、问卷追溯、复现与作者信息三个小节。

## 本次图件与附录修订（2026-11-06）

Figure 2直接引用组员提供的 `figures/lca_boundary_group.pdf`，文件内容与交付PDF一致。LaTeX裁去外围留白，保留全部图内内容。图表生成器保留该PDF并重建其他三张图；源文件包包含当前图件。此前绘图脚本、旧PDF与旧SVG为历史资产。

原附录A曾包含来源定位、问卷追溯、复现与作者信息三个小节；精简版本将其合并到正文末尾。本次在参考文献后恢复附录结构，更新文件路径和当前分析口径。原始问卷、模型参数、全部八个编号公式及数值结果维持原有版本。

## 本次正文与排版修订（2026-11-05）

补充租赁交通敏感性分析的依据，并报告交通在租赁排放、支出和主动时间中的占比（60.5%、44.4%、92.3%）。正文恢复年度排放的寿命分摊、清洗次数、交通活动量及数值代入；补充归一化参考值的情景来源、综合评分示例与排名交叉点的求解式。个人与群体CR的解释分别对应个人判断和聚合判断。

三张表统一使用10 pt字号、内容自适应列宽与居中对齐；表1拆分复合项目，每个单元格单行显示。表格生成器同步保存列格式。原始问卷、模型参数、数值代码、结果数据与四张图保持原有版本。

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

源文件包包含正文、参考文献、实际引用的表图，以及技术路线图的可编辑SVG、组员提供的LCA系统边界原始PDF与图件说明，解压后可直接编译。`delivery_manifest.json`记录LaTeX、PDF和源文件包的SHA-256。代码、原始数据和完整结果随GitHub仓库提供；源文件包用于独立排版编译。

## 本轮结果

环境、成本和便利性权重为0.2410、0.4295和0.3295。二手、新品和租赁的综合分为0.8412、0.8281和0.5189。个人CR达标11/17，群体CR为0.005885。租赁相对二手、新品的交通临界值为基准交通负担的约6.87%和10.67%；计算维持同一组AHP权重及评分参考值。

论文基于原始问卷和已归档证据。参数变更后，请重算并同步核对正文中的数值陈述。

已通过14项模型检查、309条交通情景的独立核验和全部页面视觉检查；编译日志中的引用与版面检查通过。详见`validation.json`。

技术路线图另提供[可编辑SVG](figures/framework.svg)和[高分辨率预览](figures/framework.png)。运行`python -X utf8 -B report/draw_framework.py`可单独重建此图。

LCA系统边界图为[组员提供的PDF](figures/lca_boundary_group.pdf)。运行 `python -X utf8 -B report/generate_assets.py` 时保留此图。旧 `draw_lca_boundary.py` 及对应SVG属于历史图件，说明见[图件来源与复现记录](lca_boundary_notes.md)。
