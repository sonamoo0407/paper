"""Package only application code, reviewed Scholar source and docs; exclude data/secrets/venvs."""
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
target = root.parent / ("root-paper-lab-transfer-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + ".zip")
dirs = ["root_paper_lab", "skills", "scripts", "tests", "vendor/scholar-search-mcp"]
files = ["pyproject.toml", "README.md", "VALIDATION.md", "디스코드_전달문.md"]
with ZipFile(target, "x", compression=ZIP_DEFLATED) as z:
    for name in files:
        z.write(root / name, "root-paper-lab/" + name)
    for name in dirs:
        for p in (root / name).rglob("*"):
            if p.is_file() and not any(x in p.parts for x in [".git", "__pycache__", ".env", ".venv"]):
                z.write(p, "root-paper-lab/" + p.relative_to(root).as_posix())
with ZipFile(target) as z:
    assert z.testzip() is None
    assert not any("/runs/" in n or "/.venv/" in n or "/.git/" in n for n in z.namelist())
print(str(target))
