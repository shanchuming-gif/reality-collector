import requests
import re
import socket
import urllib.parse

# 1. 逻辑源：高熵原始数据池
SOURCES = [
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/v2rayng-wg.txt"
]

def check_node(node_url):
    """
    物理级体检：解析节点并尝试 TCP 握手
    """
    try:
        # 解析 VLESS 链接逻辑
        parsed = urllib.parse.urlparse(node_url)
        # 提取服务器地址和端口
        server_info = parsed.netloc.split('@')[-1]
        address, port = server_info.split(':')
        
        # 尝试建立 TCP 连接，超时设为 2.5 秒（追求效率与准确的平衡）
        socket.setdefaulttimeout(2.5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((address, int(port)))
        return True
    except:
        return False

def logical_desalt():
    print("开始逻辑脱盐：正在抓取原始节点...")
    raw_nodes = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            # 筛选 Reality 特征节点
            nodes = re.findall(r'vless://.*reality.*', res.text, re.IGNORECASE)
            raw_nodes.extend(nodes)
        except:
            continue
    
    unique_nodes = list(set(raw_nodes))
    print(f"抓取完成，共发现 {len(unique_nodes)} 个潜在节点。开始自动体检...")

    # 2. 自动化质检：剔除失效节点
    valid_nodes = []
    for index, node in enumerate(unique_nodes):
        if check_node(node):
            valid_nodes.append(node)
            print(f"[{index+1}] 节点存活：通过检测")
        else:
            print(f"[{index+1}] 节点死亡：逻辑剔除")

    # 3. 输出负熵结果
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_nodes))
    
    print(f"--- 逻辑处理完毕 ---")
    print(f"原始节点: {len(unique_nodes)} | 存活节点: {len(valid_nodes)}")
    print(f"可用节点已固化至 output.txt")

if __name__ == "__main__":
    logical_desalt()
