"""ComfyUI native HTTP API for submit and history query."""

import json
import os
import uuid
from typing import Any, Optional

import httpx
from comfykit.comfyui.http_executor import HttpExecutor

from cli_comfyui.config import CliConfig
from cli_comfyui.output import from_execute_result, result_to_dict


def _build_executor(config: CliConfig) -> HttpExecutor:
    api_key = config.comfyui_api_key or None
    return HttpExecutor(base_url=config.comfyui_url, api_key=api_key)


async def submit_workflow(
    config: CliConfig,
    workflow_path: str,
    params: dict[str, Any],
) -> str:
    """Submit workflow to ComfyUI queue without waiting (selfhost only)."""
    executor = _build_executor(config)
    if not os.path.exists(workflow_path):
        raise FileNotFoundError(f"Workflow file does not exist: {workflow_path}")

    metadata = executor.get_workflow_metadata(workflow_path)
    if not metadata:
        raise ValueError("Cannot parse workflow metadata")

    with open(workflow_path, encoding="utf-8") as f:
        workflow_data = json.load(f)

    workflow_data = await executor._apply_params_to_workflow(
        workflow_data, metadata, params or {}
    )
    workflow_data, _ = executor._randomize_seed_in_workflow(workflow_data)

    client_id = str(uuid.uuid4())
    prompt_ext_params: dict[str, Any] = {}
    if executor.api_key:
        prompt_ext_params = {
            "extra_data": {
                "api_key_comfy_org": executor.api_key,
            }
        }

    return await executor._queue_prompt(workflow_data, client_id, prompt_ext_params)


async def fetch_history_result(
    config: CliConfig,
    prompt_id: str,
    include_queue: bool = False,
) -> dict[str, Any]:
    """Fetch execution result from ComfyUI history (single poll)."""
    executor = _build_executor(config)
    base_url = executor.base_url.rstrip("/")

    headers: dict[str, str] = {}
    if executor.api_key:
        headers["Authorization"] = f"Bearer {executor.api_key}"

    queue_data: Optional[dict[str, Any]] = None
    async with httpx.AsyncClient(timeout=30.0) as client:
        if include_queue:
            queue_resp = await client.get(f"{base_url}/queue", headers=headers)
            if queue_resp.status_code == 200:
                queue_data = queue_resp.json()

        history_resp = await client.get(f"{base_url}/history/{prompt_id}", headers=headers)
        if history_resp.status_code != 200:
            return result_to_dict(
                status="failed",
                prompt_id=prompt_id,
                msg=f"History request failed: HTTP {history_resp.status_code}",
                queue=queue_data,
            )

        history_data = history_resp.json()

    if prompt_id not in history_data:
        return result_to_dict(
            status="pending",
            prompt_id=prompt_id,
            msg="Task not found in history (may still be running)",
            queue=queue_data,
        )

    prompt_history = history_data[prompt_id]
    status_block = prompt_history.get("status")
    if status_block and status_block.get("status_str") == "error":
        messages = status_block.get("messages") or []
        errors = [
            body.get("exception_message")
            for msg_type, body in messages
            if msg_type == "execution_error" and isinstance(body, dict)
        ]
        error_message = "\n".join(e for e in errors if e) or "Unknown error"
        return result_to_dict(
            status="failed",
            prompt_id=prompt_id,
            msg=error_message,
            queue=queue_data,
        )

    if "outputs" not in prompt_history:
        return result_to_dict(
            status="running",
            prompt_id=prompt_id,
            msg="Task in history but outputs not ready",
            queue=queue_data,
        )

    from comfykit.comfyui.models import ExecuteResult

    result = ExecuteResult(
        status="completed",
        prompt_id=prompt_id,
        outputs=prompt_history["outputs"],
    )

    output_id_2_var: dict[str, str] = {}
    output_id_2_images: dict[str, list[str]] = {}
    output_id_2_videos: dict[str, list[str]] = {}
    output_id_2_audios: dict[str, list[str]] = {}
    output_id_2_texts: dict[str, list[str]] = {}

    for node_id, node_output in prompt_history["outputs"].items():
        images, videos, audios = executor._split_media_by_suffix(node_output, base_url)
        if images:
            output_id_2_images[node_id] = images
        if videos:
            output_id_2_videos[node_id] = videos
        if audios:
            output_id_2_audios[node_id] = audios
        if "text" in node_output:
            texts = node_output["text"]
            if isinstance(texts, str):
                texts = [texts]
            elif not isinstance(texts, list):
                texts = [str(texts)]
            output_id_2_texts[node_id] = texts

    if output_id_2_images:
        result.images_by_var = executor._map_outputs_by_var(output_id_2_var, output_id_2_images)
        result.images = executor._extend_flat_list_from_dict(result.images_by_var)
    if output_id_2_videos:
        result.videos_by_var = executor._map_outputs_by_var(output_id_2_var, output_id_2_videos)
        result.videos = executor._extend_flat_list_from_dict(result.videos_by_var)
    if output_id_2_audios:
        result.audios_by_var = executor._map_outputs_by_var(output_id_2_var, output_id_2_audios)
        result.audios = executor._extend_flat_list_from_dict(result.audios_by_var)
    if output_id_2_texts:
        result.texts_by_var = executor._map_outputs_by_var(output_id_2_var, output_id_2_texts)
        result.texts = executor._extend_flat_list_from_dict(result.texts_by_var)

    data = from_execute_result(result)
    if queue_data is not None:
        data["queue"] = queue_data
    return data
