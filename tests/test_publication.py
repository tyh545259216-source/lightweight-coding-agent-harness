import json
import os
import subprocess

from scripts.public_audit import audit, inventory


def test_public_scan_reports_locations_without_secret_values(tmp_path):
    credential = "sk-" + "a" * 32
    host = "D:" + chr(92) + "private" + chr(92) + "notes"
    (tmp_path / "README.md").write_text(credential + "\n" + host, encoding="utf-8")
    report = audit(tmp_path)
    assert {finding["rule"] for finding in report["findings"]} == {
        "openai_key",
        "absolute_host_path",
    }
    assert credential not in json.dumps(report)
    assert host not in json.dumps(report)


def test_private_evidence_excluded_and_preserved(tmp_path):
    private = tmp_path / "eval/results/raw/session.jsonl"
    private.parent.mkdir(parents=True)
    private.write_text("private original", encoding="utf-8")
    public = tmp_path / "eval/public/bad_cases_v2.jsonl"
    public.parent.mkdir(parents=True)
    public.write_text('{"task_id":"bad","success":false}', encoding="utf-8")
    assert inventory(tmp_path) == [public]
    assert audit(tmp_path)["findings"] == []
    assert private.read_text() == "private original"


def test_public_export_does_not_walk_escaping_directory_links(tmp_path):
    root, outside = tmp_path / "public", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.py").write_text("private original", encoding="utf-8")
    link = root / "src"
    if os.name == "nt":
        process = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True
        )
        assert process.returncode == 0
    else:
        link.symlink_to(outside, target_is_directory=True)
    assert inventory(root) == []
    assert (outside / "secret.py").read_text() == "private original"
