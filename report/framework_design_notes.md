# 技术路线图的文献依据与绘图说明

本次重绘查看了下列论文的原图，以核对研究阶段、输入输出和并行模块的组织方式。新版图依据本研究的方法独立绘制，图形和文字均为本研究定制。

| 参考研究 | 实际查看的图 | 组织方式及本图借鉴点 |
|---|---|---|
| Amasawa et al. (2023), *Can rental platforms contribute to more sustainable fashion consumption? Evidence from a mixed-method study* | Fig. 2，PDF第5页；同时查看Fig. 1 | 服装购买与租赁比较；用输入参数、环境评价和输出指标构成清晰路径。借鉴短标签、明确指标单位和输入/计算/输出分层。[DOI](https://doi.org/10.1016/j.clrc.2023.100103) |
| Monticelli & Costamagna (2023), *Environmental assessment of the rental business model: a case study for formal wear* | Figs. 1–2，PDF第5–6页 | 礼服购买与租赁比较；上层生命周期阶段对应下层过程，租赁活动使用局部循环。借鉴阶段标题与内部模块的层级。[DOI](https://doi.org/10.1007/s10668-022-02363-x) |
| Johnson & Plepys (2021), *Product-Service Systems and Sustainability: Analysing the Environmental Impacts of Rental Clothing* | Fig. 2，PDF第7页 | 共同生产链与购买/租赁两条分支，外层边界和内部过程采用不同线型。借鉴共同情景与并行计算模块。[DOI](https://doi.org/10.3390/su13042118) |
| Hannouf & Assefa (2018), *A Life Cycle Sustainability Assessment-Based Decision-Analysis Framework* | Fig. 1，PDF第6页 | 将生命周期评价与决策分析分成两个层次，以前者的计算结果作为后者输入。借鉴评价结果进入综合决策的模块衔接。[DOI](https://doi.org/10.3390/su10113863) |

前三篇主要提供系统边界图和LCA模型图；第四篇提供生命周期评价与决策分析的整合框架。本研究将这些组织原则用于专属技术路线，内容包括统一研究情景、年度LCA/LCC和主动时间、原始问卷AHP权重、综合评分及交通敏感性分析。

## 与研究模型的对应

- 统一情景为一名NUS学生一年六次正式活动，比较新品、二手和同款租赁。
- 排放、费用和主动时间由年度模型计算；原始17份完整问卷用于AHP准则权重。
- AHP采用1、2、3比率映射，完整样本几何聚合，并报告CR。
- 各指标经线性归一化后按AHP权重加总。
- 交通参数α调整租赁的交通排放、费用和时间；综合评分使用固定AHP权重。

## 视觉编码

彩色版本借鉴用户提供的会议论文示意图截图中的彩色模块、圆角框、虚线分组和图标提示。配色与图标依据本研究独立绘制：青绿、蓝色和琥珀色分别标识LCA、LCC和主动时间，紫色连接偏好获取与AHP加权评分，暖色模块组织交通敏感性分析。三种获取方案具有相同大小与视觉权重。礼服、循环箭头、衣架、叶片、钱币、时钟和问卷图标均保留为可编辑矢量元素，模块名称完整标注其含义。

虚线框表示分析分组，实线箭头表示计算衔接。问卷权重直接进入综合评分，交通归属比例只改变租赁负担；固定权重与评分参考值的说明保留。图幅为6.8×3.8英寸，正文标签约8–9.4 pt。研究内容、公式、问卷样本数及模型结果沿用已核对版本。

## 文件与复现

- `draw_framework.py`：独立矢量绘图脚本。
- `figures/framework.pdf`：论文使用的矢量图。
- `figures/framework.svg`：可编辑文本与形状的矢量图。
- `figures/framework.png`：高分辨率预览图。

在项目根目录运行`python -X utf8 -B report/generate_assets.py`可重建全部论文图表，也可单独运行`python -X utf8 -B report/draw_framework.py`重建技术路线图。文献原图保留在本次查阅的临时资料中；仓库提供来源链接与原创图的复现代码。
