import asyncio
import json
import sys
from typing import Any

RUNNER_SCRIPT = """
import sys, json, importlib.util

payload = json.loads(sys.stdin.read())
spec = importlib.util.spec_from_file_location("skill", payload["file_path"])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fn = getattr(module, payload["function_name"])
result = fn(**payload["args"])
print(json.dumps(result))
"""


async def run_skill(file_path: str, function_name: str, args: dict, timeout: int = 30) -> Any:
    payload = json.dumps(
        {"file_path": file_path, "function_name": function_name, "args": args}
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            RUNNER_SCRIPT,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(payload.encode()), timeout=timeout
        )
        if proc.returncode != 0:
            return {"error": "skill_error", "message": stderr.decode()[:500]}
        return json.loads(stdout.decode())
    except asyncio.TimeoutError:
        proc.kill()
        return {"error": "skill_timeout", "message": f"Skill exceeded {timeout}s timeout"}
    except Exception as e:
        return {"error": "skill_error", "message": str(e)}
