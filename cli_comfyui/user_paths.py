"""Cross-platform user config directory for cli-comfyui."""

from __future__ import annotations

import json
import os
import platform
import sys
from importlib import resources
from pathlib import Path
from typing import Literal

APP_NAME = "comfyui-cli"
CONFIG_FILENAME = "config.json"
WORKFLOWS_DIRNAME = "workflows"


def get_platform_kind() -> Literal["macos", "windows", "linux", "other"]:
    system = sys.platform
    if system == "darwin":
        return "macos"
    if system == "win32":
        return "windows"
    if system.startswith("linux"):
        return "linux"
    return "other"


def get_config_dir() -> Path:
    """
    User-level config directory (independent of current working directory).

    macOS / Linux:  ~/.config/comfyui-cli/
    Windows:        %APPDATA%\\comfyui-cli\\
                    (fallback: %USERPROFILE%\\AppData\\Roaming\\comfyui-cli\\)
    """
    kind = get_platform_kind()
    if kind == "windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return (Path(appdata) / APP_NAME).resolve()
        return (Path.home() / "AppData" / "Roaming" / APP_NAME).resolve()

    # macOS, Linux, and other Unix-like systems
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return (Path(xdg) / APP_NAME).resolve()
    return (Path.home() / ".config" / APP_NAME).resolve()


def get_default_config_path() -> Path:
    return get_config_dir() / CONFIG_FILENAME


def get_default_workflows_dir() -> Path:
    return get_config_dir() / WORKFLOWS_DIRNAME


def get_config_path_help_lines() -> list[str]:
    """Human-readable config paths for --help (macOS vs Windows)."""
    cfg = get_config_dir()
    cfg_file = get_default_config_path()
    wf = get_default_workflows_dir()
    lines = [
        "DEFAULT CONFIG (used when -c/--config is omitted; cwd does not matter)",
        "",
        "  macOS / Linux:",
        f"    Config dir:     {cfg}",
        f"    config.json:    {cfg_file}",
        f"    workflows/:     {wf}/selfhost/  and  {wf}/runninghub/",
        "",
        "  Windows:",
        f"    Config dir:     {cfg}",
        f"    config.json:    {cfg_file}",
        f"    workflows\\:    {wf}\\selfhost\\  and  {wf}\\runninghub\\",
        "",
        f"  Detected OS: {platform.system()} ({get_platform_kind()})",
        "",
        "  First run auto-creates the directory and config.json from template.",
        "  Override:  -c /path/to/config.json",
        "  Env:       COMFYUI_CLI_CONFIG=/path/to/config.json",
    ]
    return lines


def _read_bundled_example() -> dict:
    """Load packaged config.example.json."""
    try:
        ref = resources.files("cli_comfyui").joinpath("config.example.json")
        text = ref.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError):
        # Fallback when running from source without package data
        fallback = Path(__file__).resolve().parent / "config.example.json"
        text = fallback.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Bundled config example must be a JSON object")
    return data


def init_user_config(force: bool = False) -> Path:
    """
    Create config dir, workflows subdirs, and config.json if missing.

    Returns path to config.json.
    """
    config_dir = get_config_dir()
    config_path = get_default_config_path()
    workflows_dir = get_default_workflows_dir()

    config_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / "selfhost").mkdir(parents=True, exist_ok=True)
    (workflows_dir / "runninghub").mkdir(parents=True, exist_ok=True)

    if config_path.exists() and not force:
        return config_path

    example = _read_bundled_example()
    example["workflows_dir"] = str(workflows_dir)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(example, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return config_path


def resolve_config_path(explicit: str | None) -> Path:
    """
    Resolve config file path.

    Priority:
      1. explicit -c/--config argument
      2. COMFYUI_CLI_CONFIG environment variable
      3. Default user config (auto-init if missing)
    """
    if explicit is not None:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            path = path.resolve()
        else:
            path = path.resolve()
        return path

    env_path = os.environ.get("COMFYUI_CLI_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    return init_user_config(force=False)


def ensure_config_exists(path: Path) -> Path:
    """Ensure config file exists; auto-init only for default user config path."""
    if path.exists():
        return path

    if path.resolve() == get_default_config_path().resolve():
        return init_user_config(force=False)

    raise FileNotFoundError(
        f"Config file not found: {path}\n"
        f"Default user config: {get_default_config_path()}\n"
        f"Run: comfyui-cli init"
    )
