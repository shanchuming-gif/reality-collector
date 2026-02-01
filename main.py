import requests
import re

# 逻辑源：高熵原始数据
SOURCES = [
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/v2rayng-wg.txt"
]

def logical_desalt():
    all_nodes = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            # 筛选 Reality 特征节点
            nodes = re.findall(r'vless://.*reality.*', res.text, re.IGNORECASE)
            all_nodes.extend(nodes)
        except:
            continue
    
    # 物理去重，输出负熵结果
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(list(set(all_nodes))))

if __name__ == "__main__":
    logical_desalt()
