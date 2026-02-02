import requests, re, socket, urllib.parse, ssl, concurrent.futures, yaml

# 1. 逻辑源
SOURCES = [
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/v2rayng-wg.txt",
    "https://raw.githubusercontent.com/ts-sf/v2ray-configs/main/All_Configs_Sub.txt"
]

def check_node_tls(node_url):
    """深度体检：模拟 TLS 握手"""
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
    """逻辑转换：将 VLESS 链接转换为 Clash 字典格式"""
    try:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        netloc = parsed.netloc.split('@')
        user_id = netloc[0]
        server_info = netloc[1].split(':')
        
        return {
            "name": f"Reality-{index}",
            "type": "vless",
            "server": server_info[0],
            "port": int(server_info[1]),
            "uuid": user_id,
            "cipher": "auto",
            "tls": True,
            "udp": True,
            "servername": query.get("sni", [""])[0],
            "network": query.get("type", ["tcp"])[0],
            "reality-opts": {"public-key": query.get("pbk", [""])[0], "short-id": query.get("sid", [""])[0]},
            "client-fingerprint": query.get("fp", ["chrome"])[0]
        }
    except:
        return None

def main():
    raw_content = ""
    for url in SOURCES:
        try: raw_content += requests.get(url, timeout=10).text
        except: continue
    
    raw_nodes = list(set(re.findall(r'vless://.*reality.*', raw_content, re.IGNORECASE)))
    
    # 物理脱盐：多线程探测
    valid_nodes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_node_tls, raw_nodes))
        valid_nodes = [r for r in results if r]

    # 生成 v2rayN 用的列表
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_nodes))

    # 生成 Clash 用的 YAML
    proxies = []
    for i, url in enumerate(valid_nodes):
        p = parse_vless_to_clash(url, i)
        if p: proxies.append(p)

    clash_config = {
        "port": 7890, "allow-lan": True, "mode": "rule", "log-level": "info",
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "自动选择",
                "type": "url-test", # 核心：Clash 自动挑选延迟最低的节点
                "proxies": [p["name"] for p in proxies],
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300
            },
            {"name": "手动切换", "type": "select", "proxies": ["自动选择"] + [p["name"] for p in proxies]}
        ],
        "rules": ["MATCH,自动选择"]
    }

    with open("clash_config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)

    print(f"处理完成：保留存活节点 {len(valid_nodes)} 个")

if __name__ == "__main__":
    main()
