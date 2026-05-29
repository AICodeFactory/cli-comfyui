"""init subcommand: create user config directory and config.json."""

import argparse
import json
import sys

from cli_comfyui.user_paths import (
    get_config_dir,
    get_default_config_path,
    get_default_workflows_dir,
    init_user_config,
)


def init_command(args: argparse.Namespace) -> int:
    path = init_user_config(force=args.force)
    info = {
        "status": "ok",
        "config_dir": str(get_config_dir()),
        "config_file": str(path),
        "workflows_dir": str(get_default_workflows_dir()),
        "message": "Edit config.json (comfyui_url, workflows_dir) then place workflow JSON files.",
    }
    sys.stdout.write(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    return 0


def add_parser(
    subparsers: argparse._SubParsersAction,
    parents: list[argparse.ArgumentParser] | None = None,
) -> None:
    parser = subparsers.add_parser(
        "init",
        help="Create user config dir and config.json (macOS/Windows/Linux)",
        parents=parents or [],
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing config.json with template",
    )
    parser.set_defaults(func=init_command)
