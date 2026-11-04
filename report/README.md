# English term paper

[论文 PDF](main.pdf) · [LaTeX 正文](main.tex) · [APA 7 参考文献](references.tex) · [原始问卷分析结果](analysis/results.json)

## 本轮更新

论文采用小组提供的中文摘要对应的学术英文版本，说明NUS学生一年六次正式活动的情景、LCA和LCC估算、AHP加权综合评分，以及补充交通敏感性分析的目的。

正文同时纳入已完成的原始问卷描述表、AHP对照表、交通敏感性分析及相应方法、讨论和结论。全部分析使用原18条问卷记录，其中17份具有完整的三题比较。

## 文件

- `main.tex`、`main.pdf`：12页论文。
- `references.tex`：9条参考文献，采用natbib作者—年份引用。
- `tables/`：正文引用5张外置表；模型输入表直接写在正文中。`ahp.tex`保留原始基准分析输出。
- `figures/`：研究流程、排放分解、交通敏感性分析，共3张矢量PDF图。
- `analysis/recompute.py`：从原始问卷和项目模型重算修订版分析。
- `analysis/results.json`：问卷描述、5种权重设定、基准综合分、交通交叉点及输入哈希。
- `analysis/validation.json`：独立数值与论文检查结果。
- `generate_assets.py`：原始基准图表生成器；更新全部图表时按下方顺序运行两个脚本。

## 编译

已有表图可直接编译。使用Tectonic时，在本目录执行：

```sh
tectonic main.tex
```

也可使用TeX Live或MiKTeX，执行两次：

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

参考文献直接维护在`references.tex`中。编译后检查引用、表图和分页。

## 重算

从项目根目录执行：

```sh
python -m pip install -r requirements.txt
python -m pip install numpy matplotlib
python -X utf8 -B code/run.py
python -X utf8 -B -m unittest discover -s tests -v
python -X utf8 -B report/generate_assets.py
python -X utf8 -B report/analysis/recompute.py --source-repo .
```

原始生成器先更新流程图与费用表；修订版分析脚本随后更新问卷描述、AHP对照、排名、交通临界点和分析图。`--source-repo .`明确指定当前项目为输入来源。脚本读取原始数据并将修订版输出写入`report/`；模型参数变化时，正文数值与解释需同步核对。

## 检查与解释

- 原18条问卷记录、17份完整比较及输入哈希已核对；主分析仅2份通过个人CR检验。
- 5种权重设定、15项基准综合分和10个交通交叉点经独立计算核验。
- 个人与群体一致性分别报告；问卷权重作为探索性偏好证据，提供温和映射、AIP、等权和子样本对照。
- 基准排序为二手、新品、租赁。主权重下，租赁与二手、新品的交通负担归属比例交叉点分别约为6.77%和11.15%。
- 交通阈值对应指定评分参考值，以及交通排放、费用和时间同比例变化的设定。
- 更新后的12页PDF已编译并检查引用与版面；原始模型参数和问卷回答保留。

[问卷量表核实记录](../evidence/survey_scale.md)说明Q9/Q10端点方向与中间位置的解释。六次可租性、清洗安排、本地交通和主动时间等仍作为论文披露的情景或代理数据。

可独立编译的源文件由`main.tex`、`references.tex`以及正文引用的`tables/`和`figures/`组成。源文件包为交付快照，日常编辑以展开文件为准。
