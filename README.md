# DSS5202 Group 04

比较一名学生一年参加 6 次正式活动时，购买新品复穿、购买二手复穿、每场单独租赁同款 **Love, Bonito Eyka Multi-way Satin Column Dress（S）** 的年度排放、支出和综合评分。

流程：**参数与来源 → LCA → LCC → AHP 权重 → 标准化评分与排名 → 解释**。

## 入口

- [论文 PDF](report/main.pdf) · [LaTeX 正文](report/main.tex) · [参考文献](report/references.tex)
- [论文编译、检查摘要及待核实事项](report/README.md)
- [自动计算结果与解释](results/report.md)

## 目录

```text
├── code/           # model.py、ahp.py、run.py：计算与结果导出
├── data/           # parameters.json、sources.json 与 raw/ 原始资料
├── evidence/       # 报价、时间假设、问卷量表核实与文献图表证据
├── results/        # 重算生成的 CSV、结果报告和输入哈希清单
├── report/         # 论文 PDF、LaTeX、图表、生成脚本及源文件包
├── tests/          # 10 项计算与来源检查
├── requirements.txt
└── README.md
```

## 重算

Python 3.10+；模型依赖 openpyxl，论文制图另需 matplotlib。

```sh
python -m pip install -r requirements.txt
python -B code/run.py
python -B -m unittest discover -s tests -v
python report/generate_assets.py
```

`results/annual_results.csv` 保存排放、费用及主动时间分解；`ahp_individual.csv`、`ahp_group.csv` 保存个人和群体 AHP；`rankings.csv` 保存评分与排名；`survey_input.csv` 仅导出匿名 ID、原行号及三题回答；`run_manifest.json` 记录输入哈希和环境。

## 固定口径

- 制造、分销与处置统一按年度 6 次 / 终身 26 次分摊；二手此前 1 次仅用于剩余寿命检查。0.478 kg 是文献参考质量，不再额外乘算。
- 购买清洗 7 次、租赁 6 次，采用同一清洗代理因子。购买分摊 1 车公里配送；租赁为 240 人公里轨道交通，不叠加购买配送。
- 金额为 SGD；购买计完整购衣款，押金假设全退并排除净成本，转售与残值为 0。
- 18 条问卷记录中 17 份完整，主映射个人仅 2/17 通过 CR。群体几何聚合判断，RI=0.52、CR≤0.10；全部完整回答为探索性主分析，合格子样本另报。
- [Q9/Q10 原问卷量表已核实](evidence/survey_scale.md)：端点方向与代码一致；中间位置只有数字，1/3/5 比率转换为研究设定。
- 年度参考上限 24 kgCO₂e、360 SGD、1080 分钟；评分为 1−负担/上限，不截断。购买 120 / 租赁 780 分钟为主动时间假设。

## 小组协作

每项修改建议建立独立分支，通过 Pull Request 讨论、审核并合入 `main`。修改参数或代码后须重算、测试，并按论文目录说明更新图表及 PDF。源文件包是交付快照，日常编辑以展开的源文件为准。

仓库含原始问卷、提案及作者信息，建议保持私有，仅邀请组员；不提交密钥、虚拟环境或编译缓存。Git 历史及原始资料保留。
