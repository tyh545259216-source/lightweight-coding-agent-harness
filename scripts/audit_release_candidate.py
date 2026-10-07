"""Audit a declared release allowlist and local Markdown links; never publishes."""

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

from public_audit import HOST_PATH, SECRET_RULES

FORBIDDEN = {"work", ".venv", "__pycache__", ".sessions", ".traces", ".harness", "blobs", "models", ".pytest_cache", ".mypy_cache", ".ruff_cache", "raw-sessions", "raw-traces", "benchmark-cache", "coverage-temp"}
EXTENSIONS = {".gguf", ".bin", ".safetensors", ".pt", ".pth", ".onnx", ".pyc", ".pem", ".key"}


def unsafe(path: Path) -> bool:
    return bool(set(path.parts) & FORBIDDEN) or path.suffix.lower() in EXTENSIONS or path.name in {".env", ".coverage"}


def audit(root: Path) -> dict:
    root = root.resolve()
    names = json.loads((root / "release_files.json").read_text(encoding="utf-8"))["files"]
    findings = []
    links = []
    for name in names:
        relative = Path(name)
        path = root / relative
        if relative.is_absolute() or ".." in relative.parts or unsafe(relative):
            findings.append({"file": name, "rule": "forbidden_export_path"})
            continue
        if not path.is_file() or path.is_symlink() or path.is_junction() or not path.resolve().is_relative_to(root):
            findings.append({"file": name, "rule": "missing_or_escaping_file"})
            continue
        text = path.read_text(encoding="utf-8")
        for rule, pattern in {**SECRET_RULES, "absolute_host_path": HOST_PATH}.items():
            for match in pattern.finditer(text):
                findings.append({"file": name, "line": text.count("\n", 0, match.start()) + 1, "rule": rule})
        if path.suffix == ".md":
            for match in re.finditer(r"\[[^\]\n]*\]\(([^)\n]+)\)", text):
                target = match.group(1).strip().strip('<>')
                if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith('#'):
                    continue
                target = unquote(target.split('#')[0])
                dest = (path.parent / target).resolve()
                if not dest.is_relative_to(root) or not dest.exists():
                    links.append({"file": name, "target": target})
    tracked = []
    status = "NOT_A_GIT_CHECKOUT; clean export"
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True)
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root:
        status = "SCANNED"
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split('\0')
    forbidden_tracked = [name for name in tracked if name and unsafe(Path(name))]
    return {"files": len(names), "secret_path_findings": findings, "broken_links": links, "git_index_status": status, "tracked_files": len([x for x in tracked if x]), "forbidden_tracked": forbidden_tracked, "scope": "Declared public files only; generated ignored outputs are not publication files", "remote_ci": "NOT RUN"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(bool(result['secret_path_findings'] or result['broken_links'] or result['forbidden_tracked']))
