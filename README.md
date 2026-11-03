# DSS5202：三种服装获取方案的年度比较

研究一名学生一年参加6次正式活动时，买一件新品复穿、买一件二手复穿、每场单独租赁同款的差异。来源中的商品名为 **Love, Bonito Eyka Multi-way Satin Column Dress（S）**；“Eykq”按报价拼写更正，中等档次为研究定位。

唯一流程：**参数与来源 → 年度LCA → 年度LCC → 问卷AHP → 标准化与排名 → 解释**。

## 小组协作

论文入口：[PDF](report/main.pdf)、[LaTeX 正文](report/main.tex)、[参考文献](report/references.tex)。继续完善前先看 [待补充信息](report/pending_information.md) 和 [验证记录](report/verification.md)。

克隆仓库后，建议每项修改建立独立分支，通过 Pull Request 讨论、审核并合入 `main`：

```sh
git switch main
git pull --ff-only
git switch -c improve-report
# 修改、检查后提交
git add <修改的文件>
git commit -m "Describe the improvement"
git push -u origin improve-report
```

修改模型参数或代码后，请重算结果、运行测试，再按 [论文编译说明](report/README.md) 更新图表和 PDF；修改正文数字时须与结果核对。`report/DSS5202_Group04_LaTeX_Source.zip` 是上传前的源文件快照，后续编辑以仓库内展开的文件为准。

仓库包含原始问卷、提案以及作者信息，建议保持私有，仅邀请组员协作。不要将密钥、访问令牌、虚拟环境或编译缓存提交到仓库。

## 运行

在本目录执行（Python 3.10+）：

```sh
python -m pip install -r requirements.txt
python code/run.py
python -m unittest discover -s tests -v
```

已在现有 `/opt/anaconda3/bin/python`（Python 3.13.5、openpyxl 3.1.5）运行通过，无需安装新依赖。入口也支持从其他目录按绝对路径执行。只依赖openpyxl；不再需要NumPy、绘图、优化求解器或Word/PDF构建工具。

## 目录

```text
├── README.md
├── requirements.txt
├── data/
│   ├── parameters.json       # 唯一模型参数，含单位、来源和事实/假设分类
│   ├── sources.json          # 报价、文献、问卷和方法来源索引
│   └── raw/                  # 原问卷、提案、文献PDF、报价/服务/因子快照
├── evidence/                 # 所用文献图表、报价摘录和旧时间配置证据
├── code/
│   ├── model.py              # LCA、LCC、时间、标准化与加权排名
│   ├── ahp.py                # 直接从原工作簿生成个人及群体矩阵
│   └── run.py                # 唯一运行入口与CSV/报告导出
├── tests/test_calculations.py
└── results/                  # 年度分解、个人/群体AHP、排名及报告
```

先阅读 [自动结果与解释](results/report.md)。`annual_results.csv`保存五阶段排放、五项支出和主动时间分解；`ahp_individual.csv`保存个人矩阵的三个独立比较、权重及CR；`ahp_group.csv`和`rankings.csv`包含完整样本/CR合格子样本及温和映射。`survey_input.csv`仅含匿名ID、原行号与三题回答，不导出时间戳或个人信息。

## 计算口径

- 三种方式总寿命统一26次，制造/分销/处置按6/26分摊；二手此前穿1次仅检查剩余寿命。0.478 kg仅为文献参考，不再乘重量。
- 购买初洗1次加穿后6洗，租赁归还后6洗，均使用0.109代理。租赁取还为240人公里轨道情景；购买按20车公里/20件分摊，租赁不叠加配送。
- 报价币种经项目原始记录核对为 **SGD**，本轮未刷新市场页面。购买全价一次支付，押金假设全退、排除成本；基准零转售和残值。
- 18份原始记录中17份AHP完整。主映射为研究者5/3/1转换；Q9反向。个人用3×3行几何均值（等价主特征向量），群体几何聚合判断；RI=0.52、CR≤0.10。主分析保留全部完整回答，另报合格子样本；主映射个人仅2/17通过CR，结论为探索性。
- 年度参考上限24 kgCO₂e、360 SGD、1080分钟为研究设定；分数=1−年度负担/年度上限，不截断。权重与最终结果在运行时计算，CSV保留精度。
- 原时间配置确有购买15+7×15=120、租赁6×(10+4×30)=780分钟，均为研究者主动时间假设，尚无实测支持。租赁实际清洗、额外普通护理费及Q9/Q10完整标签等缺口见报告。

## 清理范围

旧v1/v2模型与参数合为一套；问卷/AHP及评分链路合为三个模块。删除混合方案优化、预算约束、帕累托前沿、扩展敏感性、备选商品计算、旧论文构建、任务/交接/重复说明、缓存及过期输出。来源中与本研究有关的证据保留；Sandin PDF移入`data/raw/`，原问卷与提案内容未改。

具体删除路径、原SHA-256、证据迁移和计数见`results/cleanup_manifest.json`；验证结果见`results/verification.json`。清理仅作用于本项目目录，未触碰旁边的任务包、其他工作目录或版本控制记录；清理时本目录及其父目录未发现Git仓库。
