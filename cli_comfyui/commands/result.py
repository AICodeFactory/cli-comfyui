"""result subcommand: query workflow execution result by prompt_id."""

import argparse
import asyncio
import json
from pathlib import Path

from loguru import logger

from cli_comfyui.comfyui_api import fetch_history_result
from cli_comfyui.config import load_config
from cli_comfyui.output import OutputFormat, emit_result


def result_command(args: argparse.Namespace) -> int:
    """Execute result subcommand."""
    config_path = Path(args.config).resolve()
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.error(str(exc))
        return 1

    if not config.comfyui_url:
        logger.error("comfyui_url is required in config for result queries")
        return 1

    try:
        data = asyncio.run(
            fetch_history_result(
                config,
                args.prompt_id,
                include_queue=args.queue,
            )
        )
    except Exception as exc:
        logger.error(str(exc))
        return 1

    fmt: OutputFormat = args.format
    emit_result(data, fmt, args.output)

    status = data.get("status")
    if status == "completed":
        return 0
    if status in ("pending", "running"):
        return 2
    return 1


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "result",
        help="Query workflow result by prompt_id (selfhost ComfyUI)",
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
        "--prompt-id",
        required=True,
        help="ComfyUI prompt_id returned from run --no-wait",
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Include current /queue status in output",
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
    parser.set_defaults(func=result_command)
