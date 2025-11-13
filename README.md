# AskEcho Excel 批处理脚本

`batch_excel_agent.py` 用于批量读取 Excel 中的每一条问题，调用 Feedcoop Agent Chat Completion 接口生成回答，并把答案和“首帧返回时间”(first-token latency) 写回到 Excel 中，方便对大模型的响应速度与输出质量做统一评估。

## 功能特性
- **流式推理**：使用 SSE 流式接口，在接收到第一段内容时立即记录首帧耗时。
- **列位灵活**：问题、答案、首帧耗时列均可配置，未指定耗时列时自动写在答案列右侧。
- **错误回写**：连续重试失败后，会在答案列写入 `[ERROR] ...` 以便排查。
- **限速与重试**：支持请求间隔、最大重试次数、重试等待间隔等参数，便于规避限流。

## 依赖环境
- Python 3.9+
- `requests`, `openpyxl`

建议使用虚拟环境：
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 快速开始
```powershell
python batch_excel_agent.py \
  --bot-id <BOT_ID> \
  --api-key <API_KEY> \
  --input 输入.xlsx \
  --output 输出.xlsx \
  --question-column A \
  --answer-column B \
  --latency-column C
```
若不指定 `--output`，会自动写入 `<输入名>_processed.xlsx`；若省略 `--latency-column`，默认把耗时写在答案列右侧。

## CLI 参数
| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--bot-id` | Feedcoop 机器人 ID | 必填 |
| `--api-key` | Feedcoop API Key (Bearer) | 必填 |
| `--input` | 输入 Excel 路径 | 必填 |
| `--output` | 输出 Excel 路径 | `<输入名>_processed.xlsx` |
| `--sheet-name` | 要处理的 Sheet 名称 | 工作簿当前激活表 |
| `--question-column` | 问题列（字母） | `A` |
| `--answer-column` | 答案列（字母） | `B` |
| `--latency-column` | 首帧耗时列（秒），可不填 | 答案列的右侧一列 |
| `--start-row` | 起始行号 | `2` |
| `--skip-completed` | 若答案列已有内容则跳过 | 关闭 |
| `--request-interval` | 每次调用后的等待秒数 | `0.2` |
| `--max-retries` | 失败重试次数（>=1） | `3` |
| `--retry-wait` | 重试前的等待秒数 | `2.0` |
| `--temperature` | 传给模型的 temperature | 不设置 |
| `--timeout` | HTTP 请求超时时间（秒） | `60` |

## 工作流程
1. 打开输入工作簿，定位到指定列与起始行。
2. 若 `--skip-completed` 开启且答案列已有内容，则跳过该行。
3. 通过 `AgentClient` 调用 Feedcoop API：
   - 以流式方式逐行读取 `data:` 事件；
   - 接到第一段内容时记录 `time.perf_counter()` 计算首帧耗时；
   - 拼接所有增量片段形成完整回答。
4. 成功则把答案和首帧耗时（秒，保留三位小数）写回相应列。
5. 失败会重试；重试仍失败则把错误写入答案列，耗时列清空。
6. 所有行处理完毕后保存到输出路径，并打印“已处理/跳过/失败”统计。

## 输出格式
- **答案列**：模型完整输出；失败时为 `[ERROR] ...`。
- **首帧耗时列**：首帧到达耗时（秒），示例 `0.742`；若未收到内容则为空。

## 常见问题
- **Excel 正在占用**：确保 Excel 文件未被桌面程序打开，否则 `openpyxl` 无法写入。
- **HTTP 报错/invalid_request**：检查 Bot ID、API Key、网络及代理；必要时增大 `--timeout`。
- **频繁超时**：适当调大 `--request-interval`、`--retry-wait`，或减少同时运行的任务。

## 实用建议
- 先在少量行上试跑确认列名、Sheet、起始行设置正确。
- 若要记录更多指标，可在 Excel 中预留额外列，或在脚本中扩展写入逻辑。
- 建议结合版本控制跟踪输出文件，方便对比不同 prompt 或模型的效果与耗时。
