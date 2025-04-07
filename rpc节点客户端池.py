import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import pandas as pd


def enhanced_check(url):
    """节点有效性检测（POST请求验证）"""
    try:
        response = requests.post(
            url,
            json={"jsonrpc": "2.0", "method": "web3_clientVersion", "params": [], "id": 1},
            headers={"Content-Type": "application/json"},
            timeout=8,
            verify=False
        )
        return response.status_code == 200 and "jsonrpc" in response.text
    except:
        return False


def export_to_excel(result):
    """导出结果到Excel"""
    data = []
    for chain_id, urls in result.items():
        for url in urls:
            data.append({
                "Chain ID": chain_id,
                "RPC URL": url,
                "检测时间": time.strftime("%Y-%m-%d %H:%M:%S")
            })

    pd.DataFrame(data).to_excel("可用节点信息.xlsx", index=False, engine="openpyxl")
    print("检测结果已保存到：可用节点信息.xlsx")


def run_detection():
    """执行节点探测"""
    # 准备检测任务
    nodes_to_check = [
        (chain["chainId"], url)
        for chain in chains
        if isinstance(chain, dict)
        for url in chain.get("rpc", [])
        if url.startswith("http")
    ]

    # 多线程检测(十条)
    available = []
    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=10) as executor:  # 保持10个线程
        futures = [
            executor.submit(
                lambda args: (args[0], args[1], enhanced_check(args[1])),
                (cid, url)
            )
            for cid, url in nodes_to_check
        ]

        for future in futures:
            cid, url, status = future.result()
            if status:
                with lock:
                    available.append((cid, url))

    # 整理的结果
    result = defaultdict(list)
    for cid, url in available:
        result[cid].append(url)

    # 输出统计信息
    print(f"检测完成，共发现 {len(available)} 个可用节点")
    print(f"涉及 {len(result)} 条不同的区块链")

    # 导出Excel
    export_to_excel(result)


if __name__ == "__main__":
    # 获取链数据
    chains = requests.get('https://chainid.network/chains_mini.json', timeout=10).json()

    # 执行检测
    run_detection()