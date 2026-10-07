"""Observational execution checks; scripted transport is not model capability evidence."""

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest

from mini_harness.providers.base import Message

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location(
    "v3_observed_test", SCRIPT_DIR / "v3_observed_provider.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.asyncio
async def test_observation_preserves_request_and_provider_result(tmp_path):
    seen = []

    def respond(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "evidence", "tool_calls": []}, "finish_reason": "stop"}
                ],
                "usage": {
                    "prompt_tokens": 7,
                    "completion_tokens": 2,
                    "completion_tokens_details": None,
                },
            },
        )

    provider = module.ObservedProvider(
        "http://localhost/v1", "qwen3:4b", tmp_path / "observations.jsonl"
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    async with provider:
        response = await provider.complete([Message(role="user", content="inspect")], [])
    assert response.content == "evidence"
    assert seen[0]["stream"] is False
    assert seen[0]["max_tokens"] == 512
    assert seen[0]["reasoning_effort"] == "none"
    assert "think" not in seen[0]
    observation = json.loads((tmp_path / "observations.jsonl").read_text())
    assert observation["status"] == "COMPLETE"
    assert observation["response_timeout_observation"] == "NOT_APPLICABLE_COMPLETE_RESPONSE"
    assert observation["observed_completion_tokens"] == 2
    assert observation["ttft"] == "UNAVAILABLE"
    assert observation["reasoning_tokens"] == "UNAVAILABLE"


@pytest.mark.asyncio
async def test_stream_observation_does_not_mutate_response_bytes():
    original = b'{"choices":[{"message":{"content":"answer"},"finish_reason":"length"}],"usage":{"completion_tokens":512}}'
    row = {"first_response_body_chunk": "UNAVAILABLE", "body_bytes_observed": 0}
    import time

    wrapped = module.ObservedStream(httpx.ByteStream(original), row, time.perf_counter())
    received = b"".join([chunk async for chunk in wrapped])
    assert received == original
    assert row["finish_reason"] == "length"
    assert row["wire_usage"]["completion_tokens"] == 512


@pytest.mark.asyncio
async def test_cancellation_preserves_unavailable_usage(tmp_path):
    async def blocked(request):
        raise asyncio.CancelledError()

    provider = module.ObservedProvider(
        "http://localhost/v1", "qwen3:4b", tmp_path / "observations.jsonl"
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(blocked))
    async with provider:
        with pytest.raises(asyncio.CancelledError):
            await provider.complete([Message(role="user", content="inspect")], [])
    row = json.loads((tmp_path / "observations.jsonl").read_text())
    assert row["status"] == "CANCELLED_BY_RUNTIME"
    assert row["ttft"] == "UNAVAILABLE"
    assert "observed_completion_tokens" not in row
    assert row["body_bytes_observed"] == 0


def test_atomic_result_and_fsync_journal(tmp_path):
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import run_v3_batch

        path = tmp_path / "case" / "result.json"
        run_v3_batch.save(path, {"success": False, "failure": "timeout"})
        assert json.loads(path.read_text()) == {"success": False, "failure": "timeout"}
        assert not path.with_suffix(".pending").exists()
        module.durable_jsonl(tmp_path / "progress.jsonl", {"success": False})
        assert json.loads((tmp_path / "progress.jsonl").read_text()) == {"success": False}
    finally:
        sys.path.remove(str(SCRIPT_DIR))


@pytest.mark.asyncio
async def test_existing_lock_prevents_intent_inspection(tmp_path, monkeypatch):
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import run_v3_batch

        monkeypatch.setattr(run_v3_batch, "ROOT", tmp_path)
        lock = tmp_path / "work/v3-batch.lock"
        lock.parent.mkdir()
        lock.write_text('{"pid":123}')

        class Args:
            model = "qwen3:4b"

        with pytest.raises(FileExistsError):
            await run_v3_batch.run(Args())
        assert lock.read_text() == '{"pid":123}'
        assert not (tmp_path / "eval").exists()
    finally:
        sys.path.remove(str(SCRIPT_DIR))


@pytest.mark.asyncio
async def test_resume_keeps_completed_timeout_without_model_retry(tmp_path, monkeypatch, capsys):
    import hashlib
    from types import SimpleNamespace

    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import run_v3_batch

        monkeypatch.setattr(run_v3_batch, "ROOT", tmp_path)
        monkeypatch.setattr(run_v3_batch, "load_tasks", lambda path: [])
        monkeypatch.setattr(run_v3_batch, "load_real_tasks", lambda root: [])
        protocol = tmp_path / "eval/protocol_v3.json"
        protocol.parent.mkdir()
        protocol.write_text('{"hashes":{}}')
        (protocol.parent / "protocol_v3_diagnostic.json").write_text(
            json.dumps(
                dict(
                    parent_protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),
                    task_ids=["fixed-case"],
                    variant="FULL_V3",
                    runner={},
                )
            )
        )
        result = (
            tmp_path
            / "eval/results/v3-batched/qwen3-1.7b/diagnostic/cases/original/FULL_V3/0/fixed-case/result.json"
        )
        result.parent.mkdir(parents=True)
        payload = json.dumps(
            dict(
                variant="FULL_V3",
                repeat=0,
                task_id="fixed-case",
                success=False,
                stop_reason="timeout",
            )
        )
        result.write_text(payload)
        forged = result.parent / "artifacts/FULL_V3/0/fixed-case/workspace/result.json"
        forged.parent.mkdir(parents=True)
        forged.write_text('{"untrusted_workspace_file":true}')

        class NeverCallProvider:
            def __init__(self, *args, **kwargs):
                raise AssertionError("Completed failures must not call provider")

        monkeypatch.setattr(run_v3_batch, "ObservedProvider", NeverCallProvider)
        args = SimpleNamespace(
            model="qwen3:1.7b",
            group="diagnostic",
            resume=True,
            batch_size=5,
            task_filter=None,
            start_from=None,
            run_id="original",
        )
        await run_v3_batch.run(args)
        assert result.read_text() == payload
        assert not (result.parent / "intent.json").exists()
        assert '"attempted": 0' in capsys.readouterr().out
        assert not (tmp_path / "work/v3-batch.lock").exists()
    finally:
        sys.path.remove(str(SCRIPT_DIR))


@pytest.mark.asyncio
async def test_empty_message_is_not_reported_as_complete_final_decision(tmp_path):
    def respond(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": " \n", "tool_calls": []}, "finish_reason": "stop"}
                ]
            },
        )

    provider = module.ObservedProvider(
        "http://localhost/v1", "qwen3:1.7b", tmp_path / "observations.jsonl"
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    async with provider:
        result = await provider.complete([Message(role="user", content="inspect")], [])
    assert result.content == " \n"
    row = json.loads((tmp_path / "observations.jsonl").read_text())
    assert row["status"] == "COMPLETE"
    assert row["parsed_response_kind"] == "EMPTY_RESPONSE"
    assert row["has_parsed_decision"] is False
    assert row["final_response_complete"] == "UNAVAILABLE"
    assert row["tool_call_complete"] == "UNAVAILABLE"
