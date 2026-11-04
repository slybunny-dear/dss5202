"""Package the LaTeX source and its referenced assets for an independent build."""
from pathlib import Path
import hashlib
import json
import re
from zipfile import ZIP_DEFLATED, ZipFile


HERE = Path(__file__).resolve().parent


def package():
    main = (HERE / "main.tex").read_text(encoding="utf-8")
    paths = {HERE / "main.tex", HERE / "references.tex", HERE / "README.md"}
    for relative in re.findall(r"\\input\{([^}]+)\}", main):
        path = HERE / relative
        paths.add(path if path.suffix else path.with_suffix(".tex"))
    for relative in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", main):
        paths.add(HERE / relative)
    paths.add(HERE / "figures/framework.svg")
    paths.add(HERE / "framework_design_notes.md")
    paths.add(HERE / "figures/lca_boundary.svg")
    paths.add(HERE / "lca_boundary_notes.md")
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    destination = HERE / "DSS5202_Group04_LaTeX_Source.zip"
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, path.relative_to(HERE).as_posix())
    manifest = {
        "main_pdf_sha256": hashlib.sha256((HERE / "main.pdf").read_bytes()).hexdigest(),
        "main_tex_sha256": hashlib.sha256((HERE / "main.tex").read_bytes()).hexdigest(),
        "source_zip_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "source_files": [path.relative_to(HERE).as_posix() for path in sorted(paths)],
    }
    (HERE / "delivery_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    package()
