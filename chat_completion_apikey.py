#!/usr/bin/env python3
import argparse
import json

import requests

Host = "open.feedcoopapi.com"
Path = "/agent_api/agent/chat/completion"
ContentType = "application/json"


def request(method, body, api_key):
    header = {"Authorization": f"Bearer {api_key}", "content_type": ContentType,}
    r = requests.request(method=method,
                         url="https://{}{}".format(Host, Path),
                         headers=header,
                         params={},
                         json=body, stream=True
                         )
    if r.status_code == 200:
        stream_resp = []
        total_content = ""
        for line in r.iter_lines():
            if line:
                line_str = line.decode('utf - 8')
                if "invalid_request" in line_str:
                    print(f"请求错误，状态码: {r.status_code}， 报错：{r.text}")
                elif line_str.startswith("data:"):
                    stream_resp.append(line_str)
                    # 流式帧
                    print(line_str)
                    data = line_str[len("data:"):].strip()
                    if data not in ["[DONE]", "done"]:
                        total_content += json.loads(data)["choices"][0]["delta"]["content"]
        print(f"流式回复内容：\n{total_content}")
    else:
        print(f"请求错误，状态码: {r.status_code}， 报错：{r.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot_id", required=True, help="BOT ID")
    parser.add_argument("--api_key", required=True, help="APIKey")

    args = parser.parse_args()

    body = {
        "bot_id": args.bot_id,
        "messages": [
            {
                "role": "user",
                "content": "今天深圳的天气如何"
            }
        ],
        "stream": True,
    }
    request("POST", body, args.api_key)
