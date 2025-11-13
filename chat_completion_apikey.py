#!/usr/bin/env python3
"""
基于 API Key 的 Chat Completions 流式调用示例。

功能概述：
- 通过 HTTP(S) 请求调用 `open.feedcoopapi.com` 的聊天补全接口。
- 以流式（Server-Sent Events）方式读取增量内容，并在终端逐步打印，同时累计完整回复。

使用方式（命令行）：
    python chat_completion_apikey.py --bot_id <你的BOT_ID> --api_key <你的API_KEY>
"""

import argparse  # 解析命令行参数
import json      # 解析服务端返回的 JSON 数据

import requests  # 进行 HTTP 请求

# 目标服务的主机与路径（按服务端文档配置）
Host = "open.feedcoopapi.com"
Path = "/agent_api/agent/chat/completion"

# 请求体/响应体采用 JSON 格式
ContentType = "application/json"


def request(method, body, api_key):
    """
    以流式方式调用聊天补全接口，并打印/汇总增量内容。

    参数：
    - method: HTTP 方法字符串，例如 "POST"
    - body:   请求 JSON 体（包含 bot_id、messages、stream 等）
    - api_key: 鉴权所用的 API Key（以 Bearer 方式传入）
    """
    # 组装请求头。注意通用做法是使用 "Content-Type"（首字母大写且中间横杠），
    # 这里沿用原字段名以保持与现有代码一致。
    header = {
        "Authorization": f"Bearer {api_key}",  # 认证：Bearer Token
        "content_type": ContentType,            # 内容类型（服务端若严格区分大小写可改为 Content-Type）
    }

    # 发起 HTTP 请求，开启 stream=True 以逐行读取响应（SSE/流式）
    r = requests.request(
        method=method,
        url="https://{}{}".format(Host, Path),  # 拼接完整 URL
        headers=header,
        params={},
        json=body,
        stream=True,
    )

    # 响应码 200 视为成功，其它打印错误信息后返回
    if r.status_code == 200:
        stream_resp = []     # 保存原始的流式行（可用于调试）
        total_content = ""   # 累计模型增量内容，最终形成完整回复

        # iter_lines() 可逐行迭代响应体，常用于处理 SSE 或分块传输
        for line in r.iter_lines():
            if not line:
                continue  # 跳过空行（SSE 心跳/分隔）

            # 修正解码：必须为 'utf-8'，否则可能报错
            line_str = line.decode('utf-8')

            # 如果服务端以纯文本告知请求非法，可在此拦截并提示。
            if "invalid_request" in line_str:
                print(f"请求错误，状态码: {r.status_code}，报错：{r.text}")
                continue

            # SSE 规范常以 "data:" 开头承载一帧数据。
            if line_str.startswith("data:"):
                stream_resp.append(line_str)  # 记录原始行，便于排查问题

                # 打印原始流帧，直观查看增量（可按需关闭）
                print(line_str)

                # 去掉前缀并裁剪空白，得到 JSON 字符串或特殊标记
                data = line_str[len("data:"):].strip()

                # 流结束标记，常见为 [DONE] 或 done
                if data in ["[DONE]", "done"]:
                    continue

                # 解析 JSON 数据结构，累加增量内容片段
                try:
                    payload = json.loads(data)
                    delta = payload["choices"][0]["delta"].get("content", "")
                    total_content += delta
                except Exception as e:
                    # 若某帧不是预期 JSON 结构，打印以便定位
                    print(f"解析流数据失败：{e}，原始数据：{data}")

        # 输出最终汇总的完整回复内容
        print(f"流式回复内容：\n{total_content}")
    else:
        # 非 200 场景打印状态码与原始文本，便于排查鉴权/参数问题
        print(f"请求错误，状态码: {r.status_code}，报错：{r.text}")


if __name__ == "__main__":
    # 构建命令行解析器，要求传入 bot_id 与 api_key
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot_id", required=True, help="BOT ID")
    parser.add_argument("--api_key", required=True, help="APIKey")

    args = parser.parse_args()

    # 组织请求体：
    # - messages: 聊天上下文（此处仅一条用户消息作为示例）
    # - stream:   True 表示开启流式返回
    body = {
        "bot_id": args.bot_id,
        "messages": [
            {
                "role": "user",
                "content": "今天深圳的天气如何？",
            }
        ],
        "stream": True,
    }

    # 发起请求
    request("POST", body, args.api_key)
