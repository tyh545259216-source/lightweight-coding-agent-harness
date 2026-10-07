"""Audit an explicit public inventory; preserve all private originals and bad cases."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "README.md",
    "PLAN.md",
    "AGENTS.md",
    "LICENSE",
    ".env.example",
    "CONTRIBUTING.md",
    ".gitignore",
    ".gitattributes",
    "pyproject.toml",
    "requirements-lock.txt",
    "FINAL_REPORT_V2.md",
}
SCRIPTS = {
    "setup.ps1",
    "build_dataset_v2.py",
    "run_experiments_v2.py",
    "collect_results_v2.py",
    "public_audit.py",
    "package_public.py",
    "report_v2.py",
}
ANALYSIS = {
    "FAILURE_ANALYSIS.md",
    "failures.csv",
    "failure_evidence.jsonl",
    "reviewed_tasks.jsonl",
    "provenance.json",
    "annotations.json",
}
SECRET_RULES = {
    "openai_key": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{24,}"),
    "github_token": re.compile(r"(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}"),
    "google_key": re.compile(r"AIza[A-Za-z0-9_-]{30,}"),
    "google_oauth": re.compile(r"ya29\.[A-Za-z0-9_-]{30,}"),
    "literal_credential": re.compile(
        r"(?i)(?:api[_-]?key|access_token|refresh_token|oauth_token)\s*[\"']?\s*[:=]\s*[\"']([A-Za-z0-9_./+-]{16,})"
    ),
    "aws_key": re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
HOST_PATH = re.compile(r"(?i)\b[A-Z]:[\\/]+")


def inventory(root=ROOT):
    candidates = [root / name for name in ROOT_FILES if (root / name).is_file()]
    for directory, extensions in [
        ("src", {".py"}),
        ("tests", {".py"}),
        ("examples", {".py"}),
        ("skills", {".md"}),
        ("docs", {".md"}),
        (".github", {".yml", ".yaml"}),
        ("eval/tasks", {".json", ".jsonl"}),
        ("eval/public", {".json", ".jsonl", ".md"}),
    ]:
        base = root / directory
        if (
            not base.exists()
            or base.is_symlink()
            or base.is_junction()
            or not base.resolve().is_relative_to(root.resolve())
        ):
            continue
        for current, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [
                name
                for name in dirs
                if name not in {"__pycache__", ".pytest_cache"}
                and not (Path(current) / name).is_symlink()
                and not (Path(current) / name).is_junction()
            ]
            candidates.extend(
                Path(current) / name for name in files if Path(name).suffix in extensions
            )
    candidates.extend(
        root / "scripts" / name for name in SCRIPTS if (root / "scripts" / name).is_file()
    )
    candidates.extend(
        root / "eval/analysis" / name
        for name in ANALYSIS
        if (root / "eval/analysis" / name).is_file()
    )
    candidates.extend(
        root / "eval" / name for name in ["protocol_v2.json"] if (root / "eval" / name).is_file()
    )
    if (root / "eval/results/ablation.json").is_file():
        candidates.append(root / "eval/results/ablation.json")
    for path in candidates:
        if (
            path.is_symlink()
            or path.is_junction()
            or not path.resolve().is_relative_to(root.resolve())
        ):
            raise ValueError("Public inventory contains escaping/link path")
    return sorted(set(candidates))


def audit(root=ROOT):
    files = inventory(root)
    findings = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        for label, pattern in {**SECRET_RULES, "absolute_host_path": HOST_PATH}.items():
            for match in pattern.finditer(text):
                # Deliberately report locations only, never the matched secret value.
                findings.append(
                    {
                        "file": relative,
                        "line": text.count("\n", 0, match.start()) + 1,
                        "rule": label,
                    }
                )
    return {
        "scope": "Explicit public export inventory; raw/private results excluded, never deleted",
        "files": len(files),
        "findings": findings,
        "hashes": {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
        },
        "limitations": [
            "pattern scanner is not an exhaustive secret detector",
            "does not redact arbitrary runtime output",
            "excluded private artifacts remain available locally",
            "no OS sandbox or network isolation",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.root.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["scope", "files", "findings"]}, indent=2))
    raise SystemExit(bool(report["findings"]))
