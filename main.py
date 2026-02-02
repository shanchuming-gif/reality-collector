import requests, re, socket, urllib.parse, ssl, concurrent.futures

# 1. 逻辑源：高熵原始数据池
SOURCES = [
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/v2rayng-wg.txt",
    "https://raw.githubusercontent.com/ts-sf/v2ray-configs/main/All_Configs_Sub.txt"
]

def check_node_tls(node_url):
    """
    深度体检：模拟 TLS 握手（最接近 Real Delay 逻辑）
    """
    try:
        parsed = urllib.parse.urlparse(node_url)
        server_info = parsed.netloc.split('@')[-1]
        address, port = server_info.split(':')
        
        # 尝试建立物理连接
        with socket.create_connection((address, int(port)), timeout=3) as sock:
            # 模拟 TLS 握手（核心步骤）
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with context.wrap_socket(sock, server_hostname=address) as ssock:
                return node_url
    except:
        return None

def main():
    print("开始抓取节点...")
    raw_content = ""
    for url in SOURCES:
        try: raw_content += requests.get(url, timeout=10).text
        except: continue
    
    # 提取符合 Reality 特征的节点
    raw_nodes = list(set(re.findall(r'vless://.*reality.*', raw_content, re.IGNORECASE)))
    print(f"原始节点: {len(raw_nodes)}，开始深度体检...")

    # 使用多线程加速（避免 GitHub Actions 超时）
    valid_nodes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_node_tls, raw_nodes))
        valid_nodes = [r for r in results if r]

    # 结果固化
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_nodes))
    print(f"物理脱盐完成：存活 {len(valid_nodes)} 个节点。")

if __name__ == "__main__":
    main()
