import requests
import re
import socket
import urllib.parse
import ssl
import concurrent.futures

# 1. 扩容逻辑源：加入更多高质量的 Reality 节点池
SOURCES = [
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/v2rayng-wg.txt",
    "https://raw.githubusercontent.com/ts-sf/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/maimun-all/vless/main/all.txt"
]

def check_node_advanced(node_url):
    """
    物理级深度检测：模拟 TLS 握手 (接近 Real Delay 逻辑)
    """
    try:
        # 解析节点
        parsed = urllib.parse.urlparse(node_url)
        server_info = parsed.netloc.split('@')[-1]
        address, port = server_info.split(':')
        
        # 配置 TLS 探测环境
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 尝试建立物理连接并进行 TLS 握手
        with socket.create_connection((address, int(port)), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=address) as ssock:
                return node_url
    except:
        return None

def logical_desalt():
    print("--- 开始自动化信息脱盐 ---")
    raw_nodes = []
    
    # 抓取数据
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            # 使用更严谨的正则提取 Reality 节点
            nodes = re.findall(r'vless://.*reality.*', res.text, re.IGNORECASE)
            raw_nodes.extend(nodes)
        except:
            continue
    
    unique_nodes = list(set(raw_nodes))
    print(f"原始矿石: {len(unique_nodes)} 个节点。开始深度体检...")

    # 使用多线程加速检测，否则 GitHub Actions 可能会超时
    valid_nodes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_node_advanced, unique_nodes))
        valid_nodes = [node for node in results if node]

    # 结果固化
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_nodes))
    
    print(f"--- 逻辑处理完毕 ---")
    print(f"检测存活: {len(valid_nodes)} 个节点。")
    print(f"结果已更新至订阅地址。")

if __name__ == "__main__":
    logical_desalt()
