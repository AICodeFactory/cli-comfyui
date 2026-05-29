"""JSON configuration loader for cli-comfyui."""

import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class CliConfig(BaseModel):
    """CLI configuration loaded from JSON."""

    comfyui_url: str = Field(default="http://127.0.0.1:8188")
    comfyui_api_key: str = Field(default="")
    runninghub_api_key: str = Field(default="")
    runninghub_instance_type: str = Field(default="")
    workflows_dir: str = Field(default="../workflows")
    timeout_seconds: int = Field(default=300)

    def apply_env_overrides(self) -> "CliConfig":
        """Apply environment variable overrides (aligned with ComfyKit)."""
        data = self.model_dump()
        env_map = {
            "comfyui_url": "COMFYUI_BASE_URL",
            "comfyui_api_key": "COMFYUI_API_KEY",
            "runninghub_api_key": "RUNNINGHUB_API_KEY",
        }
        for field, env_key in env_map.items():
            value = os.environ.get(env_key)
            if value:
                data[field] = value
        instance_type = os.environ.get("RUNNINGHUB_INSTANCE_TYPE")
        if instance_type:
            data["runninghub_instance_type"] = instance_type
        timeout = os.environ.get("RUNNINGHUB_TIMEOUT")
        if timeout:
            try:
                data["timeout_seconds"] = int(timeout)
            except ValueError:
                pass
        return CliConfig(**data)

    def resolve_workflows_dir(self, config_path: Path) -> Path:
        """Resolve workflows_dir relative to config file location."""
        workflows = Path(self.workflows_dir)
        if workflows.is_absolute():
            return workflows.resolve()
        return (config_path.parent / workflows).resolve()

    def to_comfykit_kwargs(self) -> dict[str, Any]:
        """Build ComfyKit constructor kwargs (aligned with pixelle_video/service.py)."""
        kit_config: dict[str, Any] = {}
        if self.comfyui_url:
            kit_config["comfyui_url"] = self.comfyui_url
        if self.comfyui_api_key:
            kit_config["api_key"] = self.comfyui_api_key
        if self.runninghub_api_key:
            kit_config["runninghub_api_key"] = self.runninghub_api_key
        instance_type = self.runninghub_instance_type
        if instance_type and instance_type.strip():
            kit_config["runninghub_instance_type"] = instance_type
        if self.timeout_seconds > 0:
            kit_config["runninghub_timeout"] = self.timeout_seconds
        return kit_config


def load_config(config_path: str | Path) -> CliConfig:
    """Load configuration from a JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a JSON object: {path}")

    return CliConfig(**data).apply_env_overrides()
