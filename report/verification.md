# Final verification — 3 November 2026 (Singapore)

- Original project model rerun with Python 3.13.5 / openpyxl 3.1.5; all 10 existing checks passed.
- Annual emissions, expenditure and composite scores agree with recomputed CSV values within 1e-12 in the report audit.
- Main group weights: 0.2008926580071308 / 0.4793291297180824 / 0.3197782122747868. Main personal CR-qualified subset: 2 of 17; subset scores checked against existing results.
- No model, parameter, raw quote or questionnaire edits; no new optimization or sensitivity analysis.
- Tectonic 0.15.0 compilation completed with zero warnings, missing citations, missing cross-references, or overfull/underfull boxes.
- 10 pages total: 8 pages of main text including title and 185-word abstract; 1 reference page; 1 appendix page.
- All 10 final PDF pages rendered with PyMuPDF and visually inspected for tables, equations, figure labels, pagination, references, margins and clipping. Text boundary checks passed.
- Seven cited external items exactly match seven reference entries. Source publication metadata and the retained 1994/2023 volume-year choices were checked; market prices remain the frozen project observations, not a new price check.
- Figures are vector PDFs, with source Python and generated LaTeX tables included. The full paper can compile from the source package without the original survey.
- PDF SHA-256: `203d14669e63844a5d4c920a9058535c7015e3f7a47fcbb1072ccd92db0abee6`

Pending author/course metadata and unresolved evidence gaps are listed in `pending_information.md` and disclosed in the paper. This is a computational/document check, not a claim of completed human author review.

Title-page revision: removed the course/group identification and report/date lines at the user’s request; rebuilt PDF, checked the revised first page and retained 10-page pagination.
