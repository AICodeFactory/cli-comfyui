"""run subcommand: execute ComfyUI workflows."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from loguru import logger

from cli_comfyui.comfyui_api import submit_workflow
from cli_comfyui.config import CliConfig, load_config
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
    config_path = Path(args.config).resolve()
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


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "run",
        help="Execute a ComfyUI workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        help="Path to JSON config file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "-w",
        "--workflow",
        required=True,
        help="Workflow key (e.g. selfhost/image_flux.json) or file path",
    )
    parser.add_argument(
        "-p",
        "--params",
        default=None,
        help='Workflow parameters as JSON string, e.g. \'{"prompt":"a cat"}\'',
    )
    parser.add_argument(
        "--params-file",
        default=None,
        help="Path to JSON file with workflow parameters",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Submit only (selfhost); print prompt_id without waiting",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write result JSON to file instead of stdout",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.set_defaults(func=run_command)
