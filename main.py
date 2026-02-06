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

def check_node_tls(node_url):
    try:
        parsed = urllib.parse.urlparse(node_url)
        server_info = parsed.netloc.split('@')[-1]
        address, port = server_info.split(':')
        with socket.create_connection((address, int(port)), timeout=3) as sock:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with context.wrap_socket(sock, server_hostname=address) as ssock:
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

        # --- 核心修复：校验 short-id (sid) ---
        # REALITY sid 必须是偶数长度的十六进制，且最大16位。如果不符合，强制设为空字符串。
        if sid:
            if not re.fullmatch(r'[0-9a-fA-F]{2,16}', sid) or len(sid) % 2 != 0:
                sid = "" 

        proxy = {
            "name": f"Reality-{index:03d}",
            "type": "vless",
            "server": server_info[0],
            "port": int(server_info[1]),
            "uuid": user_id,
            "cipher": "auto",
            "tls": True,
            "udp": True,
            "servername": sni,
            "network": query.get("type", ["tcp"])[0],
            "reality-opts": {
                "public-key": pbk,
                "short-id": sid
            },
            "client-fingerprint": fp
        }
        if flow: proxy["flow"] = flow
        return proxy
    except:
        return None

def main():
    raw_content = ""
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            raw_content += res.text
        except: continue
    
    raw_nodes = list(set(re.findall(r'vless://.*reality.*', raw_content, re.IGNORECASE)))
    
    valid_nodes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_node_tls, raw_nodes))
        valid_nodes = [r for r in results if r]

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_nodes))

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
                "name": "自动选择",
                "type": "url-test",
                "proxies": [p["name"] for p in proxies],
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300
            },
            {
                "name": "手动切换",
                "type": "select",
                "proxies": ["自动选择"] + [p["name"] for p in proxies]
            }
        ],
        "rules": ["MATCH,自动选择"]
    }

    with open("clash_config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    main()
