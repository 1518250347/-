# AskEcho Excel 批处理智能体

## 项目简介
- 通过调用大语言模型，对 Excel 中的多行数据进行批量处理（问答、摘要、改写、结构化等），并将结果写回到 Excel。
- 使用基于 API Key 的对话补全接口（Chat Completions）。
- 示例工作簿：`测试.xlsx`。

## 目录结构
- `batch_excel_agent.py`：批量读取与写回 Excel 的主脚本。
- `chat_completion_apikey.py`：以 API Key 调用聊天模型的封装。
- `chat_completion_aksk.py`（如存在）：替代鉴权方式示例。
- `测试.xlsx`：示例输入文件。
- `requirements.txt`：依赖列表。

## 环境要求
- Python 3.9+
- 建议使用虚拟环境（venv 或 conda）

## 快速开始
1) 克隆与进入项目
```
git clone <你的仓库地址>
cd askecho_demo
```

2) 创建并激活虚拟环境（Windows PowerShell）
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3) 安装依赖
```
pip install -r requirements.txt
```

4) 配置 API Key（至少其一）
- 临时（当前终端会话）：
```
$env:OPENAI_API_KEY="<你的_api_key>"
```
- 或在系统环境变量中永久配置；若项目支持 `.env`，也可写入：
```
OPENAI_API_KEY=<你的_api_key>
```

5) 准备 Excel 输入
- 使用仓库内 `测试.xlsx`，或替换为你自己的文件。
- 确认列名与脚本读取的一致（例如：问题列、输出列、工作表名等）。

## 使用方法
> 注意：以下参数为常见示例，占位请按你脚本的实际参数名调整。

- 基本运行：
```
python batch_excel_agent.py --input 测试.xlsx --output 结果.xlsx
```

- 常见参数：
- `--sheet`：输入工作表名称（默认首个工作表）
- `--model`：模型名称（如 `gpt-4o-mini`）
- `--prompt`：提示词模板（系统/用户提示）
- `--col-in`：输入列名（如 `问题`）
- `--col-out`：输出列名（如 `回答`）

- 示例：
```
python batch_excel_agent.py --input 测试.xlsx --col-in 问题 --col-out 回答 --output 结果.xlsx --model gpt-4o-mini
```

## 环境变量
- 必需：
  - `OPENAI_API_KEY`：对话模型的 API Key
- 可选：
  - `OPENAI_API_BASE`：自定义 API Base（代理或兼容服务时使用）
  - 其他与提供商相关的变量，视 `chat_completion_apikey.py` 支持而定

## 常见问题
- 首次使用 SSH 推送到 GitHub 出现主机指纹确认：
  - 输入 `yes` 即可，指纹会被写入 `~/.ssh/known_hosts`。
- 推送报错 “Permission denied (publickey)”：
  - 将远程改为 HTTPS，或正确生成/添加 SSH Key 到 GitHub。
- Windows 出现 CRLF/LF 警告：
  - 正常提示。若需统一行尾，可在仓库根添加 `.gitattributes`：`* text=auto eol=lf`，然后执行 `git add --renormalize .`。
- Excel 文件被占用导致读写失败：
  - 先关闭已打开的 Excel 文件后再运行脚本。
- API 报错或耗时较长：
  - 检查 `OPENAI_API_KEY`、网络可达性、模型名称与 API Base；酌情增加重试与超时设置。

## 开发计划（可选）
- 增加重试与退避策略，提升稳健性。
- 增加进度条与日志输出。
- 支持按行动态提示词模板与并发限速控制。

## 许可
- 请根据实际选择并补充许可证（例如 MIT）。

## 贡献
- 欢迎提交 Issue 或 Pull Request。建议附最小可复现的示例 Excel 与复现步骤。

