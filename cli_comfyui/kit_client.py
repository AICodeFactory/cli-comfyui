"""ComfyKit client wrapper for blocking workflow execution."""

from typing import Any

from comfykit import ComfyKit
from comfykit.comfyui.models import ExecuteResult

from cli_comfyui.config import CliConfig
from cli_comfyui.workflow import WorkflowInfo


async def execute_workflow(
    config: CliConfig,
    workflow: WorkflowInfo,
    params: dict[str, Any],
) -> ExecuteResult:
    """Execute workflow via ComfyKit (blocking until complete)."""
    kit = ComfyKit(**config.to_comfykit_kwargs())
    try:
        if workflow.is_runninghub:
            workflow_input = workflow.workflow_id
        else:
            workflow_input = workflow.path
        return await kit.execute(workflow_input, params)
    finally:
        try:
            await kit.close()
        except Exception:
            pass
