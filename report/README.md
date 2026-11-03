# DSS5202 Group 04 — English term paper

本目录仅交付论文。`main.pdf` 是编译版，`main.tex` 为主源文件，`references.tex` 为可编辑的 APA 7 参考文献，`figures/` 为矢量 PDF 图，`tables/` 为结果生成的 LaTeX 表。

## 编译

已有图表可直接编译，无需访问原始问卷、联网刷新报价或运行 Python：

```sh
cd report
tectonic --keep-logs --outdir build main.tex
cp build/main.pdf main.pdf
```

也可使用完整 TeX Live/MiKTeX：

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Tectonic 首次编译可能联网获取宏包，后续可使用缓存。所需包在 `main.tex` 前导区列明。引用使用 `natbib` 的作者—年份机制，参考文献直接维护在 `references.tex`，按 APA 7 排序、作者和标题格式呈现；不需要 BibTeX/Biber。更改引用时需同步维护引用键和条目。

## 重算与更新图表

在项目根目录运行（Python 3.10+）：

```sh
python code/run.py
python -m unittest discover -s tests -v
python report/generate_assets.py
```

模型依赖为 openpyxl；图表脚本额外需要 matplotlib。正文使用当前冻结结果，若未来修改参数，需同步检查正文中的解释性数字；图表和表格会从 CSV 更新。PDF 可用 PyMuPDF 或 Poppler 渲染逐页检查。

## 文件说明

- `main.tex`：8 页正文（含标题与摘要），之后另起参考文献与附录。
- `references.tex`：7 条可核验来源；网页检索日期沿用原证据，不伪称重新观察报价。
- `generate_assets.py`：从既有年度结果、群体 AHP、排名 CSV 生成 3 张表、2 张矢量图。
- `figures/`、`tables/`：直接编译所需资源；图形可从 Python 源脚本编辑。
- `verification.md`：最终计算与 PDF 检查记录。
- `pending_information.md`：简短待补充清单。

作者姓名与学号来自 `../data/raw/proposal-group4.docx`。仅保留与论文有关的信息，不复制电话号码或问卷身份数据。

写作表达参考用户指定目录中的 Jiang et al. CVPR 论文：按研究问题组织方法与结果、给公式编号、图表附解释性图注；未使用会议模板、双栏格式、出版标识或其学术内容。

本次范围依用户最新指示限定为三固定方案的 LCA—LCC—AHP—评分链；早期提案中的优化及其他扩展没有被写成已完成结果。
