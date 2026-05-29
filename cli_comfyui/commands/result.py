"""result subcommand: query workflow execution result by prompt_id."""

import argparse
import asyncio
import json
from pathlib import Path

from loguru import logger

from cli_comfyui import help_text
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
        help=help_text.SUBCOMMAND_SUMMARY["result"],
        description=help_text.RESULT_DESCRIPTION,
        epilog=help_text.RESULT_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        metavar="FILE",
        help="JSON config; must include comfyui_url for /history API",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logs to stderr",
    )
    parser.add_argument(
        "--prompt-id",
        required=True,
        metavar="ID",
        help=(
            "ComfyUI prompt_id (UUID). From run --no-wait response.prompt_id "
            "or blocking run response.prompt_id"
        ),
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Include ComfyUI GET /queue body in response.queue (optional)",
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
    parser.set_defaults(func=result_command)
