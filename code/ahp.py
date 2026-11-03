"""Read original workbook locally; compute individual and aggregated AHP."""
import math
from openpyxl import load_workbook
from model import ROOT, values


def matrix(ec, ev, cv):
    return [[1, ec, ev], [1/ec, 1, cv], [1/ev, 1/cv, 1]]


def weights_cr(a, ri):
    if len(a) != 3 or any(len(row) != 3 for row in a) or ri <= 0 or not math.isfinite(ri):
        raise ValueError("AHP requires a 3x3 matrix and positive RI")
    for i in range(3):
        for j in range(3):
            if not math.isfinite(a[i][j]) or a[i][j] <= 0 or not math.isclose(a[i][j]*a[j][i], 1):
                raise ValueError("Expected a finite positive reciprocal matrix")
    # For positive reciprocal 3x3 matrices this is the principal eigenvector.
    geom = [math.exp(sum(math.log(x) for x in row)/3) for row in a]
    w = [x/sum(geom) for x in geom]
    ratios = [sum(a[i][j]*w[j] for j in range(3))/w[i] for i in range(3)]
    lam = sum(ratios)/3
    if not all(math.isclose(x, lam, rel_tol=1e-10) for x in ratios):
        raise ArithmeticError("Eigenvector residual failed")
    ci = max(0., (lam-3)/2)  # floating-point noise at exact consistency only
    return w, lam, ci, ci/ri


def ratio(code, strength, numerator_at_one):
    if isinstance(code, bool):
        raise ValueError("Boolean survey code")
    value = float(code)
    if not math.isfinite(value) or value != int(value) or not 1 <= value <= 5:
        raise ValueError(f"Invalid survey code: {code}")
    value = int(value)
    sign = (1 if value < 3 else -1 if value > 3 else 0) * (1 if numerator_at_one else -1)
    return strength[abs(value-3)] ** sign


def compute(config):
    opts = config["ahp"]
    p = values(config)
    wb = load_workbook(ROOT / "data/raw/survey_18.xlsx", read_only=True, data_only=False)
    try:
        sheet = wb[opts["sheet"]]
        raw = []
        for source_row, cells in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
            if all(v is None for v in cells):
                continue
            answers = {q: cells[col-1] for q, col in opts["columns"].items()}
            raw.append(dict(respondent_id=f"R{len(raw)+1:03d}", source_row=source_row, **answers))
        questions = [{"cell": cell, "text": wb[opts["question_sheet"]][cell].value}
                     for cell in opts["question_cells"]]
    finally:
        wb.close()
    individual, groups = [], []
    for mapping, strength in opts["mappings"].items():
        matrices = {}
        for row in raw:
            complete = all(row[q] not in (None, "") for q in opts["columns"])
            item = dict(respondent_id=row["respondent_id"], source_row=row["source_row"],
                        mapping=mapping, **{q: row[q] for q in opts["columns"]}, complete=complete,
                        e_over_c="", e_over_v="", c_over_v="", w_E="", w_C="", w_V="",
                        lambda_max="", ci="", cr="", cr_pass=False,
                        included_main=complete and mapping == opts["main_mapping"])
            ratios = [None if row[q] in (None, "") else ratio(row[q], strength, opts["numerator_at_code_1"][q])
                      for q in ("q8", "q9", "q10")]
            item.update(zip(("e_over_c", "e_over_v", "c_over_v"), ("" if x is None else x for x in ratios)))
            if complete:
                a = matrix(*ratios)
                matrices[row["respondent_id"]] = a
                w, lam, ci, cr = weights_cr(a, p["ri"])
                item.update(w_E=w[0], w_C=w[1], w_V=w[2], lambda_max=lam, ci=ci, cr=cr,
                            cr_pass=cr <= p["cr_threshold"])
            individual.append(item)
        for subset in ("all_complete", "cr_pass"):
            selected = [r for r in individual if r["mapping"] == mapping and r["complete"]
                        and (subset == "all_complete" or r["cr_pass"])]
            if not selected:
                raise ValueError(f"No respondents in {mapping}/{subset}; cannot aggregate")
            group = [[math.exp(sum(math.log(matrices[r["respondent_id"]][i][j])
                                  for r in selected)/len(selected)) for j in range(3)] for i in range(3)]
            w, lam, ci, cr = weights_cr(group, p["ri"])
            groups.append(dict(mapping=mapping, subset=subset, n=len(selected),
                               w_E=w[0], w_C=w[1], w_V=w[2], lambda_max=lam, ci=ci, cr=cr,
                               ri=p["ri"], e_over_c=group[0][1], e_over_v=group[0][2], c_over_v=group[1][2],
                               respondent_ids=";".join(r["respondent_id"] for r in selected)))
    return raw, individual, groups, questions
