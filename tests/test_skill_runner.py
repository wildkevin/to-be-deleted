import pytest
import textwrap
from backend.core.skill_runner import run_skill


@pytest.mark.asyncio
async def test_skill_returns_result(tmp_path):
    skill_file = tmp_path / "my_skill.py"
    skill_file.write_text(
        textwrap.dedent(
            """
        def add_numbers(a: int, b: int) -> int:
            return a + b
    """
        )
    )
    result = await run_skill(str(skill_file), "add_numbers", {"a": 3, "b": 4})
    assert result == 7


@pytest.mark.asyncio
async def test_skill_timeout(tmp_path):
    skill_file = tmp_path / "slow.py"
    skill_file.write_text(
        textwrap.dedent(
            """
        import time
        def slow():
            time.sleep(60)
    """
        )
    )
    result = await run_skill(str(skill_file), "slow", {}, timeout=1)
    assert "error" in result


@pytest.mark.asyncio
async def test_skill_exception(tmp_path):
    skill_file = tmp_path / "bad.py"
    skill_file.write_text("def boom(): raise ValueError('oops')")
    result = await run_skill(str(skill_file), "boom", {})
    assert "error" in result
