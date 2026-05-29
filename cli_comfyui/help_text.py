"""Help text for argparse (machine- and AI-readable CLI reference)."""

from cli_comfyui.user_paths import get_config_path_help_lines


def build_main_epilog() -> str:
    config_section = "\n".join(get_config_path_help_lines())
    return f"""\
{config_section}

CONFIG JSON FIELDS (in config.json)
  comfyui_url              string  ComfyUI server, e.g. http://127.0.0.1:8188
  comfyui_api_key          string  Optional ComfyUI API key
  runninghub_api_key       string  Required for runninghub/*.json workflows
  runninghub_instance_type string  Optional RunningHub instance type
  workflows_dir            string  Absolute path recommended (set by init)
  timeout_seconds          int     RunningHub timeout (default 300)

  Env overrides: COMFYUI_BASE_URL, COMFYUI_API_KEY, RUNNINGHUB_API_KEY
  Config path override: COMFYUI_CLI_CONFIG=/path/to/config.json

WORKFLOW (-w on run)
  Key under workflows_dir:  selfhost/image_flux.json
  Or absolute path to a .json file
  selfhost: full ComfyUI API-format graph; params injected via ComfyKit DSL
  runninghub: wrapper {{"source":"runninghub","workflow_id":"..."}}

COMMON RESPONSE SCHEMA (stdout JSON)
  {{
    "status": "<see subcommand>",
    "prompt_id": "<uuid|null>",
    "images": ["<url>", ...],
    "videos": ["<url>", ...],
    "audios": ["<url>", ...],
    "texts": ["<string>", ...],
    "duration": <seconds|null>,
    "msg": "<error message|null>"
  }}

EXAMPLES (no -c needed; uses user config dir above)
  comfyui-cli init
  comfyui-cli run -w selfhost/image_flux.json -p '{{"prompt":"a cat"}}'
  comfyui-cli run -w selfhost/image_flux.json -p '{{}}' --no-wait
  comfyui-cli result --prompt-id <uuid>
"""

MAIN_DESCRIPTION = """\
comfyui-cli — execute ComfyUI workflows and query results (JSON in/out).

Subcommands:
  init    Create ~/.config/comfyui-cli (macOS/Linux) or %APPDATA%\\comfyui-cli (Windows)
  run     Submit & execute a workflow (blocking by default)
  result  Query execution result by prompt_id (selfhost only)

Config is read from a fixed per-user directory (not the current shell cwd).
Stdout is always a single JSON object unless --format text.
Exit codes: 0=success, 1=error, 2=result pending/running.
"""

RUN_DESCRIPTION = """\
Execute a ComfyUI workflow.

Modes:
  Default (blocking)  Wait until done; status=completed|failed
  --no-wait           selfhost only; submit to /prompt; status=submitted + prompt_id
"""

RUN_EPILOG = """\
REQUEST
  Required:
    -w WORKFLOW     Workflow key or path (see main help)
    -p or --params-file   Workflow input parameters (JSON object)

  Params (-p / --params-file) — keys depend on workflow DSL markers, common:
    prompt           string   Text prompt (image/video workflows)
    text             string   TTS input text
    negative_prompt  string   Negative prompt
    width, height    int      Image/video size
    seed, steps, cfg number   Sampler settings
    voice, speed     mixed    TTS workflows

  Optional:
    --no-wait       selfhost only; async submit
    -o FILE         Write JSON response to file instead of stdout
    --format json|text
    -c FILE         Override user config.json (default: see comfyui-cli --help)

RESPONSE (stdout JSON)
  Blocking run (--wait, default):
    status: "completed" | "failed"
    prompt_id: string | null
    images, videos, audios, texts: URL/string arrays (empty if none)
    duration: float seconds | null
    msg: error string | null

  Async submit (--no-wait, selfhost only):
    status: "submitted"
    prompt_id: string (use with: comfyui-cli result --prompt-id ...)
    images/videos/audios/texts: []
    duration: null
    msg: null

EXIT CODES
  0  completed or submitted
  1  failure (bad config, workflow error, status=failed)

EXAMPLES
  comfyui-cli run -w selfhost/image_flux.json -p '{"prompt":"a cute cat"}'
  comfyui-cli run -w runninghub/image_flux.json -p '{"prompt":"landscape"}'
  comfyui-cli run -w selfhost/image_flux.json -p '{}' --no-wait
"""

RESULT_DESCRIPTION = """\
Query ComfyUI execution result by prompt_id (GET /history/{prompt_id}).

selfhost only. Use prompt_id from: run --no-wait, or blocking run response.
RunningHub workflows: use blocking run only (no result subcommand).
"""

RESULT_EPILOG = """\
REQUEST
  Required:
    --prompt-id ID   UUID from run (submitted or completed)

  Optional:
    --queue          Add ComfyUI /queue snapshot under response.queue
    -o FILE          Write JSON to file
    --format json|text
    -c FILE         Override user config.json (default: see comfyui-cli --help)

RESPONSE (stdout JSON)
  Same top-level fields as run; status meanings:
    "completed"  outputs ready; images/videos/audios/texts populated
    "pending"    not in history yet (still queued or running)
    "running"    in history but outputs not ready
    "failed"     execution error or HTTP error; see msg

  When --queue:
    queue: { ComfyUI /queue JSON: queue_running, queue_pending, ... }

EXIT CODES
  0  status=completed
  1  status=failed
  2  status=pending or running (retry later)

EXAMPLES
  comfyui-cli result --prompt-id 3fa85f64-5717-4562-b3fc-2c963f66afa6
  comfyui-cli result --prompt-id <uuid> --queue
"""

SUBCOMMAND_SUMMARY = {
    "init": "Create user config directory and config.json (see --help for paths)",
    "run": "Execute workflow; output JSON result (blocking or --no-wait submit)",
    "result": "Query result by prompt_id (selfhost); output JSON status/URLs",
}
