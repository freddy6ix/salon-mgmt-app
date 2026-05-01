import asyncio
from pathlib import Path


async def deliver(content: str, output_path: str, base_dir: str) -> str:
    """Write briefing content to output_path (relative to base_dir). Returns resolved path."""
    path = (Path(base_dir) / output_path).resolve()
    await asyncio.to_thread(_write, path, content)
    return str(path)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
