# English term paper

[论文 PDF](main.pdf) · [LaTeX 正文](main.tex) · [APA 7 参考文献](references.tex) · [可独立编译的源文件包](DSS5202_Group04_LaTeX_Source.zip)

## 文件

```text
report/
├── main.tex / main.pdf
├── references.tex
├── generate_assets.py       # 读取项目 CSV，生成以下图表
├── figures/                 # 2 张矢量 PDF 图
├── tables/                  # 3 张 LaTeX 结果表
├── DSS5202_Group04_LaTeX_Source.zip
└── README.md
```

已有图表可直接编译，不需要原始问卷或 Python。`references.tex` 直接维护 APA 7 条目，使用 natbib 作者—年份引用，不需要 BibTeX/Biber。

## 编译

在本目录执行，需 Tectonic（首次可能下载宏包）：

```sh
mkdir -p build
tectonic --keep-logs --outdir build main.tex
cp build/main.pdf main.pdf
```

也可使用完整 TeX Live/MiKTeX，执行两次 `pdflatex -interaction=nonstopmode -halt-on-error main.tex`。编译后检查 PDF，确认无缺失引用、内容溢出及图表排版问题。`build/` 和编译缓存不随源文件包交付。

更新图表：在项目根目录运行 `python -B code/run.py`、现有测试，再运行 `python report/generate_assets.py`（需 matplotlib）。脚本不修改模型或问卷；若模型结果改变，正文中的解释性数字也须同步核对。正文排放展示 4 位小数、综合分 6 位，CSV 保留计算精度。

## 检查摘要

- 模型重算结果与论文一致，现有 10 项检查通过。
- 论文共 10 页：8 页正文（含标题与 185 词摘要）、1 页参考文献、1 页附录；7 条外部引用与文献条目对应。
- PDF 已逐页渲染检查，后续修订已复查相应页面；原始报价、问卷及模型数值未改动，未新增优化或敏感性分析。
- 作者姓名经用户确认，论文不显示学号；归属为 NUS 理学院，教师为 Kim Leng Poh，附录保留一句 AI 使用声明。
- 写作表达参考用户提供的 Jiang et al. CVPR 论文，未采用其内容、双栏模板或出版标识。
- [问卷核实记录](../evidence/survey_scale.md)：Q9/Q10 两端标签均已核实，中间 2–4 只有数字；解释和比率映射仍作为研究设定。

## 尚待核实

- 高个人 CR 的原因与受访者对量表的理解；量表核实没有消除仅 2/17 合格的限制。
- 如课程另有格式或 AI 声明要求，提交前对照核实。
- 六次可租性、租赁实际清洗与费用、实物状态、本地时间和交通数据仍受现有假设与代理数据限制，论文已披露。

源文件包应在论文修订后重新生成，仅收录论文源文件、图表及必要说明，并附问卷量表核实记录，不包含原始问卷。
