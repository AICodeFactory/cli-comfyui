"""Unified CLI output formatting."""

import json
import sys
from typing import Any, Literal, Optional

from comfykit.comfyui.models import ExecuteResult

OutputFormat = Literal["json", "text"]


def result_to_dict(
    status: str,
    prompt_id: Optional[str] = None,
    images: Optional[list[str]] = None,
    videos: Optional[list[str]] = None,
    audios: Optional[list[str]] = None,
    texts: Optional[list[str]] = None,
    duration: Optional[float] = None,
    msg: Optional[str] = None,
    outputs: Optional[dict[str, Any]] = None,
    queue: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build unified result dictionary for stdout."""
    data: dict[str, Any] = {
        "status": status,
        "prompt_id": prompt_id,
        "images": images or [],
        "videos": videos or [],
        "audios": audios or [],
        "texts": texts or [],
        "duration": duration,
        "msg": msg,
    }
    if outputs is not None:
        data["outputs"] = outputs
    if queue is not None:
        data["queue"] = queue
    return data


def from_execute_result(result: ExecuteResult) -> dict[str, Any]:
    """Convert ComfyKit ExecuteResult to unified dict."""
    status = result.status
    if status == "completed":
        normalized = "completed"
    elif status in ("error", "failed"):
        normalized = "failed"
    elif status == "timeout":
        normalized = "failed"
    else:
        normalized = status

    return result_to_dict(
        status=normalized,
        prompt_id=result.prompt_id,
        images=list(result.images),
        videos=list(result.videos),
        audios=list(result.audios),
        texts=list(result.texts),
        duration=result.duration,
        msg=result.msg,
        outputs=result.outputs,
    )


def emit_result(data: dict[str, Any], fmt: OutputFormat, output_path: Optional[str] = None) -> None:
    """Write result to stdout or file."""
    if fmt == "json":
        text = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        text = _format_text(data)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def _format_text(data: dict[str, Any]) -> str:
    lines = [
        f"status: {data.get('status')}",
        f"prompt_id: {data.get('prompt_id')}",
    ]
    if data.get("duration") is not None:
        lines.append(f"duration: {data.get('duration')}")
    if data.get("msg"):
        lines.append(f"msg: {data.get('msg')}")
    for key in ("images", "videos", "audios", "texts"):
        items = data.get(key) or []
        if items:
            lines.append(f"{key}:")
            for item in items:
                lines.append(f"  - {item}")
    return "\n".join(lines)
