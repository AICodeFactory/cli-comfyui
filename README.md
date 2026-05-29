# cli-comfyui

ComfyUI 工作流命令行工具：执行 Workflow、按 `prompt_id` 查询结果。配置通过 JSON 文件加载。

**仓库：** https://github.com/AICodeFactory/cli-comfyui

## 安装

### 从 GitHub 安装到其他机器（推荐）

目标机器需 **Python ≥ 3.11**。

```bash
# 安装 CLI（写入当前 Python 环境的 PATH）
pip install git+https://github.com/AICodeFactory/cli-comfyui.git

# 验证
comfyui-cli --help
```

仅安装到用户目录（无需 root）：

```bash
pip install --user git+https://github.com/AICodeFactory/cli-comfyui.git
```

指定版本/tag（发布 tag 后可用）：

```bash
pip install git+https://github.com/AICodeFactory/cli-comfyui.git@v0.1.0
```

### 克隆后本地开发安装

```bash
git clone https://github.com/AICodeFactory/cli-comfyui.git
cd cli-comfyui
uv sync          # 或: pip install -e .
```

安装后可用 `comfyui-cli`，或通过模块运行：

```bash
uv run comfyui-cli --help
uv run python -m cli_comfyui --help
```

### 离线安装（wheel）

在有网络的机器上打包：

```bash
git clone https://github.com/AICodeFactory/cli-comfyui.git
cd cli-comfyui
pip install build
python -m build
# 产物: dist/cli_comfyui-0.1.0-py3-none-any.whl
```

将 `dist/*.whl` 拷到目标机后：

```bash
pip install cli_comfyui-0.1.0-py3-none-any.whl
```

（目标机需能安装依赖，或一并离线缓存 `comfykit`、`httpx` 等 wheel。）

## 配置

**不依赖当前工作目录。** 执行任意 `--help` 或首次 `run` / `result` 时，若配置不存在会自动创建用户配置目录；也可手动初始化：

```bash
comfyui-cli init
comfyui-cli --help   # 显示本机实际配置目录与 config.json 路径
```

工作流 JSON 默认放在配置目录下的 `workflows/selfhost/` 与 `workflows/runninghub/`（`init` 或 `--help` 会自动创建）。编辑 `config.json` 中的 `comfyui_url`、`workflows_dir` 等。

覆盖默认路径：

```bash
comfyui-cli -c /path/to/config.json run ...
export COMFYUI_CLI_CONFIG=/path/to/config.json
```

`config.json` 字段说明：

| 字段 | 说明 |
|------|------|
| `comfyui_url` | 本地 ComfyUI 地址（selfhost 必填） |
| `comfyui_api_key` | ComfyUI API Key（可选） |
| `runninghub_api_key` | RunningHub API Key（云工作流） |
| `runninghub_instance_type` | RunningHub 实例类型（可选） |
| `workflows_dir` | 工作流 JSON 目录（相对 `config.json` 所在目录或绝对路径） |
| `timeout_seconds` | RunningHub 超时秒数 |

环境变量可覆盖（与 ComfyKit 一致）：`COMFYUI_BASE_URL`、`COMFYUI_API_KEY`、`RUNNINGHUB_API_KEY`。

## 命令

### `run` — 执行工作流

阻塞执行（默认，使用 ComfyKit，与 Pixelle-Video 主项目一致）：

```bash
comfyui-cli run -c config.json \
  -w selfhost/image_flux.json \
  -p '{"prompt":"a cute cat"}'
```

从文件读取参数：

```bash
comfyui-cli run -c config.json -w selfhost/image_flux.json --params-file params.json
```

仅提交、不等待（**仅 selfhost**），输出 `prompt_id`：

```bash
comfyui-cli run -c config.json \
  -w selfhost/image_flux.json \
  -p '{"prompt":"a cat"}' \
  --no-wait
```

RunningHub 云工作流（需配置 `runninghub_api_key`）：

```bash
comfyui-cli run -c config.json \
  -w runninghub/image_flux.json \
  -p '{"prompt":"a beautiful landscape"}'
```

### `result` — 查询结果

按 ComfyUI `prompt_id` 查询历史（**仅 selfhost**）：

```bash
comfyui-cli result -c config.json --prompt-id <uuid>
```

附带当前队列状态：

```bash
comfyui-cli result -c config.json --prompt-id <uuid> --queue
```

写入文件：

```bash
comfyui-cli result -c config.json --prompt-id <uuid> -o result.json
```

### 输出格式

默认 JSON。人类可读摘要：

```bash
comfyui-cli run -c config.json -w selfhost/image_flux.json -p '{}' --format text
```

### 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 1 | 失败（配置错误、执行失败等） |
| 2 | `result` 任务仍在进行（`pending` / `running`） |

## 限制说明

- `run --no-wait` 与 `result` 仅支持本地 **selfhost** ComfyUI（使用 `/prompt` 与 `/history`）。
- **RunningHub** 工作流请使用默认阻塞 `run`（不加 `--no-wait`）；异步结果查询暂未实现。

## 工作流格式

目录结构示例（需自行准备或从 [Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video) 复制 `workflows/`）：

```
workflows/
├── selfhost/*.json      # ComfyUI API 格式完整节点图
└── runninghub/*.json    # {"source":"runninghub","workflow_id":"..."}
```

在 `config.json` 中设置 `workflows_dir` 指向该目录，例如：

```json
"workflows_dir": "/opt/comfyui-workflows"
```

工作流节点标题中的 ComfyKit DSL（如 `$prompt.text!`）由 ComfyKit 在运行时注入参数。

## 与 Pixelle-Video 的关系

本仓库为独立 CLI，不依赖 `pixelle_video`。执行逻辑与 [Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video) 的 ComfyKit 用法一致；工作流 JSON 可与主项目 `workflows/` 目录共用。
