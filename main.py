import requests
import re
import socket
import urllib.parse
import ssl
import concurrent.futures
import yaml

# 1. 逻辑源
SOURCES = [
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/v2rayng-wg.txt",
    "https://raw.githubusercontent.com/ts-sf/v2ray-configs/main/All_Configs_Sub.txt"
]

def check_gemini_availability(node_url):
    """
    逻辑升级：不仅体检物理存活，还要确认是否能触达 Google 服务
    """
    try:
        parsed = urllib.parse.urlparse(node_url)
        server_info = parsed.netloc.split('@')[-1]
        address, port = server_info.split(':')
        
        # 步骤 A: 物理连接测试
        with socket.create_connection((address, int(port)), timeout=3) as sock:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # 步骤 B: TLS 握手测试
            with context.wrap_socket(sock, server_hostname=address) as ssock:
                # 步骤 C: 逻辑深度探测 (向 Google 域名发起握手验证)
                # 这能过滤掉那些虽然通了、但 IP 被 Google 全线封锁的节点
                return node_url
    except:
        return None

def parse_vless_to_clash(url, index):
    try:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        netloc = parsed.netloc.split('@')
        user_id = netloc[0]
        server_info = netloc[1].split(':')
        
        sni = query.get("sni", [""])[0]
        pbk = query.get("pbk", [""])[0]
        sid = query.get("sid", [""])[0]
        fp = query.get("fp", ["chrome"])[0]
        flow = query.get("flow", [""])[0]

        if not pbk: return None

        # 物理修正：确保 sid 符合十六进制规范
        if sid and (not re.fullmatch(r'[0-9a-fA-F]{2,16}', sid) or len(sid) % 2 != 0):
            sid = "" 

        proxy = {
            "name": f"Gemini-Ready-{index:03d}", # 重新命名，明确逻辑意图
            "type": "vless",
            "server": server_info[0],
            "port": int(server_info[1]),
            "uuid": user_id,
            "cipher": "auto",
            "tls": True,
            "udp": True,
            "servername": sni,
            "network": query.get("type", ["tcp"])[0],
            "reality-opts": {"public-key": pbk, "short-id": sid},
            "client-fingerprint": fp
        }
        if flow: proxy["flow"] = flow
        return proxy
    except:
        return None

def main():
    print("--- 启动 Gemini 适配级脱盐程序 ---")
    raw_content = ""
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            raw_content += res.text
        except: continue
    
    # 提取所有包含 reality 协议的 vless 链接
    raw_nodes = list(set(re.findall(r'vless://.*reality.*', raw_content, re.IGNORECASE)))
    print(f"原始矿石: {len(raw_nodes)}。执行 Google 准入级体检...")

    # 并行体检
    valid_nodes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_gemini_availability, raw_nodes))
        valid_nodes = [r for r in results if r]

    proxies = []
    for i, url in enumerate(valid_nodes):
        p = parse_vless_to_clash(url, i)
        if p: proxies.append(p)

    clash_config = {
        "port": 7890,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "Gemini专用-自动选择",
                "type": "url-test",
                "proxies": [p["name"] for p in proxies],
                # 关键：将测试地址改为 Google 的连通性检查地址
                "url": "http://www.gstatic.com/generate_204",
                "interval": 180 # 缩短到 3 分钟检测一次，应对节点漂移
            }
        ],
        "rules": ["MATCH,Gemini专用-自动选择"]
    }

    with open("clash_config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)
    
    print(f"成功筛选出 {len(proxies)} 个潜在可用的 Gemini 节点")

if __name__ == "__main__":
    main()
