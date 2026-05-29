"""Workflow path resolution and metadata parsing."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class WorkflowInfo:
    """Resolved workflow metadata."""

    name: str
    source: str
    path: str
    key: str
    workflow_id: Optional[str] = None

    @property
    def is_runninghub(self) -> bool:
        return self.source == "runninghub" and bool(self.workflow_id)


def parse_workflow_file(file_path: Path, source: str) -> WorkflowInfo:
    """Parse workflow JSON file (aligned with comfy_base_service._parse_workflow_file)."""
    with open(file_path, encoding="utf-8") as f:
        content: dict[str, Any] = json.load(f)

    info = WorkflowInfo(
        name=file_path.name,
        source=source,
        path=str(file_path.resolve()),
        key=f"{source}/{file_path.name}",
    )

    if "source" in content and "workflow_id" in content:
        info.workflow_id = str(content["workflow_id"])

    return info


def resolve_workflow(workflow: str, workflows_dir: Path) -> WorkflowInfo:
    """
    Resolve workflow identifier to WorkflowInfo.

    Accepts:
    - Key: selfhost/image_flux.json
    - Absolute or relative file path to a workflow JSON
    """
    workflow_path = Path(workflow)

    if workflow_path.is_file():
        return _parse_from_file(workflow_path)

    key_path = Path(workflow.replace("\\", "/"))
    if len(key_path.parts) >= 2:
        source, name = key_path.parts[0], "/".join(key_path.parts[1:])
        candidate = workflows_dir / source / name
        if candidate.is_file():
            return parse_workflow_file(candidate, source)

    candidate = workflows_dir / workflow
    if candidate.is_file():
        return _parse_from_file(candidate)

    raise FileNotFoundError(
        f"Workflow not found: {workflow} (searched under {workflows_dir})"
    )


def _parse_from_file(file_path: Path) -> WorkflowInfo:
    """Infer source from parent directory name when possible."""
    file_path = file_path.resolve()
    source = file_path.parent.name
    if source not in ("selfhost", "runninghub"):
        source = "selfhost"
    return parse_workflow_file(file_path, source)
