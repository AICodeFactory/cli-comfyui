"""run subcommand: execute ComfyUI workflows."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from loguru import logger

from cli_comfyui import help_text
from cli_comfyui.comfyui_api import submit_workflow
from cli_comfyui.config import load_config
from cli_comfyui.user_paths import resolve_config_path
from cli_comfyui.kit_client import execute_workflow
from cli_comfyui.output import OutputFormat, emit_result, from_execute_result, result_to_dict
from cli_comfyui.workflow import resolve_workflow


def _load_params(args: argparse.Namespace) -> dict[str, Any]:
    if args.params_file:
        with open(args.params_file, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Params file must contain a JSON object")
        return data
    if args.params:
        data = json.loads(args.params)
        if not isinstance(data, dict):
            raise ValueError("Params must be a JSON object")
        return data
    return {}


def run_command(args: argparse.Namespace) -> int:
    """Execute run subcommand."""
    config_path = resolve_config_path(args.config)
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.error(str(exc))
        return 1

    workflows_dir = config.resolve_workflows_dir(config_path)

    try:
        workflow = resolve_workflow(args.workflow, workflows_dir)
        params = _load_params(args)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.error(str(exc))
        return 1

    fmt: OutputFormat = args.format

    if args.no_wait:
        if workflow.is_runninghub:
            logger.error(
                "--no-wait is only supported for selfhost workflows. "
                "Use default --wait for RunningHub."
            )
            return 1
        try:
            prompt_id = asyncio.run(
                submit_workflow(config, workflow.path, params)
            )
        except Exception as exc:
            logger.error(str(exc))
            return 1

        data = result_to_dict(status="submitted", prompt_id=prompt_id)
        emit_result(data, fmt, args.output)
        return 0

    try:
        result = asyncio.run(execute_workflow(config, workflow, params))
    except Exception as exc:
        logger.error(str(exc))
        return 1

    data = from_execute_result(result)
    emit_result(data, fmt, args.output)

    if data["status"] != "completed":
        if data.get("msg"):
            logger.error(data["msg"])
        return 1
    return 0


def add_parser(
    subparsers: argparse._SubParsersAction,
    parents: list[argparse.ArgumentParser] | None = None,
) -> None:
    parser = subparsers.add_parser(
        "run",
        help=help_text.SUBCOMMAND_SUMMARY["run"],
        description=help_text.RUN_DESCRIPTION,
        epilog=help_text.RUN_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=parents or [],
    )
    parser.add_argument(
        "-w",
        "--workflow",
        required=True,
        metavar="WORKFLOW",
        help=(
            "Workflow key under workflows_dir (e.g. selfhost/image_flux.json) "
            "or path to .json; runninghub/* needs workflow_id wrapper in file"
        ),
    )
    parser.add_argument(
        "-p",
        "--params",
        default=None,
        metavar="JSON",
        help=(
            'Workflow inputs as JSON object. Example: \'{"prompt":"a cat","width":1024}\'. '
            "Keys match ComfyKit DSL in workflow node titles ($prompt, $width!, etc.)"
        ),
    )
    parser.add_argument(
        "--params-file",
        default=None,
        metavar="FILE",
        help="Path to JSON file (object) with same keys as -p/--params",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help=(
            "selfhost only: POST /prompt, return immediately. "
            'Response status="submitted" + prompt_id; poll with: result --prompt-id ID'
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="FILE",
        help="Write response JSON to FILE (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help='Output encoding: json (machine) or text (human). Default: json',
    )
    parser.set_defaults(func=run_command)
