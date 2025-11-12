#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import hmac
import json
from urllib.parse import quote

import requests

Service = "volc_torchlight_api"
Action = "ChatCompletion"
Version = "2024-01-01"
Region = "cn-north-1"
Host = "mercury.volcengineapi.com"
ContentType = "application/json"


def norm_query(params):
    query = ""
    for key in sorted(params.keys()):
        if type(params[key]) == list:
            for k in params[key]:
                query = (
                        query + quote(key, safe="-_.~") + "=" + quote(k, safe="-_.~") + "&"
                )
        else:
            query = (query + quote(key, safe="-_.~") + "=" + quote(params[key], safe="-_.~") + "&")
    query = query[:-1]
    return query.replace("+", "%20")


# 第一步：准备辅助函数。
# sha256 非对称加密
def hmac_sha256(key: bytes, content: str):
    return hmac.new(key, content.encode("utf-8"), hashlib.sha256).digest()


# sha256 hash算法
def hash_sha256(content: str):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# 第二步：签名请求函数
def request(method, body, ak, sk):
    # 第三步：创建身份证明。其中的 Service 和 Region 字段是固定的。ak 和 sk 分别代表
    # AccessKeyID 和 SecretAccessKey。同时需要初始化签名结构体。一些签名计算时需要的属性也在这里处理。
    # 初始化身份证明结构体
    date = datetime.datetime.utcnow()
    credential = {
        "access_key_id": ak,
        "secret_access_key": sk,
        "service": Service,
        "region": Region,
    }
    # 初始化签名结构体
    request_param = {
        "body": body,
        "host": Host,
        "path": "/",
        "method": method,
        "content_type": ContentType,
        "date": date,
        "query": {"Action": Action, "Version": Version},
    }
    if body is None:
        request_param["body"] = ""
    # 第四步：接下来开始计算签名。在计算签名前，先准备好用于接收签算结果的 signResult 变量，并设置一些参数。
    # 初始化签名结果的结构体
    x_date = request_param["date"].strftime("%Y%m%dT%H%M%SZ")
    short_x_date = x_date[:8]
    x_content_sha256 = hash_sha256(json.dumps(request_param["body"]))
    sign_result = {
        "Host": request_param["host"],
        "X-Content-Sha256": x_content_sha256,
        "X-Date": x_date,
        "Content-Type": request_param["content_type"],
    }
    # 第五步：计算 Signature 签名。
    signed_headers_str = ";".join(
        ["content-type", "host", "x-content-sha256", "x-date"]
    )
    canonical_request_str = "\n".join(
        [request_param["method"].upper(),
         request_param["path"],
         norm_query(request_param["query"]),
         "\n".join(
             [
                 "content-type:" + request_param["content_type"],
                 "host:" + request_param["host"],
                 "x-content-sha256:" + x_content_sha256,
                 "x-date:" + x_date,
                 ]
         ),
         "",
         signed_headers_str,
         x_content_sha256,
         ]
    )

    hashed_canonical_request = hash_sha256(canonical_request_str)

    credential_scope = "/".join([short_x_date, credential["region"], credential["service"], "request"])
    string_to_sign = "\n".join(["HMAC-SHA256", x_date, credential_scope, hashed_canonical_request])

    k_date = hmac_sha256(credential["secret_access_key"].encode("utf-8"), short_x_date)
    k_region = hmac_sha256(k_date, credential["region"])
    k_service = hmac_sha256(k_region, credential["service"])
    k_signing = hmac_sha256(k_service, "request")
    signature = hmac_sha256(k_signing, string_to_sign).hex()

    sign_result["Authorization"] = "HMAC-SHA256 Credential={}, SignedHeaders={}, Signature={}".format(
        credential["access_key_id"] + "/" + credential_scope,
        signed_headers_str,
        signature,
        )
    header = {**sign_result}
    # 第六步：将 Signature 签名写入 HTTP Header 中，并发送 HTTP 请求。
    r = requests.request(method=method,
                         url="https://{}{}".format(request_param["host"], request_param["path"]),
                         headers=header,
                         params=request_param["query"],
                         json=request_param["body"], stream=True
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
    parser.add_argument("--access_key", required=True, help="AccessKey")
    parser.add_argument("--secret_key", required=True, help="SecretKey")

    args = parser.parse_args()

    body = {
        "bot_id": args.bot_id,
        "messages": [
            {
                "role": "user",
                "content": "今天深圳的天气如何"
            }
        ],
        "stream": True
    }
    request("POST", body, args.access_key, args.secret_key)
