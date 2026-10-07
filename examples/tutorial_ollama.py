"""Optional single-attempt Ollama tutorial; model-dependent, never a benchmark."""

import asyncio

from tutorial_demo import parser, run_tutorial

if __name__ == "__main__":
    command = parser()
    command.add_argument("--model", default="qwen3:1.7b")
    command.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    args = command.parse_args()
    args.live = True
    raise SystemExit(0 if asyncio.run(run_tutorial(args)) else 2)
