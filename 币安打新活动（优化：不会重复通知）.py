import requests
import time
import schedule
import json
import os
from eth_abi import decode
from datetime import datetime
from web3 import Web3

# ******************** 配置部分 ********************
BSCSCAN_API_KEY = 'QQ53Q2GRHXK7EHT7C468KY87WTVN2RVYC2'
DINGDING_WEBHOOK = 'https://oapi.dingtalk.com/robot/send?access_token=799fc2e347ae541d6ed66c5650aa8299b0a1f3ae74348351c473731f70bfd787'
STORAGE_FILE = 'processed_txs.json'  # 持久化存储文件

FUNCTION_SIGNATURE = 'createIDO(address[],uint256[],uint8)'
METHOD_SELECTOR = '0xfd5c9779'

MONITOR_CONFIGS = [
    {
        'address': '0xe0c7897d48847b6916094bf5cd8216449ea8fb86',
        'method_selector': METHOD_SELECTOR,
        'check_success': False
    },
    {
        'address': '0x839b20f6a7f258e0137c5aa4333f7c79e3a296c5',
        'method_selector': METHOD_SELECTOR,
        'check_success': True
    }
]


# ******************** 持久化存储函数 ********************
def load_processed_txs():
    """加载已处理交易记录"""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r') as f:
                return set(json.load(f))
        except Exception as e:
            print(f"加载存储文件失败: {str(e)}，将创建新文件")
    return set()


def save_processed_txs():
    """保存已处理交易记录"""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(list(processed_txs), f)
    except Exception as e:
        print(f"保存存储文件失败: {str(e)}")


processed_txs = load_processed_txs()


# ******************** 核心功能函数 ********************
def get_transactions(address):
    """获取指定地址的交易记录"""
    url = 'https://api.bscscan.com/api'
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': 0,
        'endblock': 99999999,
        'sort': 'desc',
        'apikey': BSCSCAN_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data['status'] == '1':
            return data['result']
        print(f"API错误: {data['message']}")
        return []
    except Exception as e:
        print(f"API请求异常: {str(e)}")
        return []


def decode_dynamic_array(param_bytes, start_pos, param_type):
    """动态数组解析"""
    # 读取数组长度
    length_bytes = param_bytes[start_pos:start_pos + 32]
    if len(length_bytes) != 32:
        raise ValueError("无效的数组长度字节")

    length = decode(['uint256'], length_bytes)[0]
    elements = []
    elements_start = start_pos + 32  # 跳过长度字段

    for i in range(length):
        element_start = elements_start + i * 32
        element_end = element_start + 32

        if element_end > len(param_bytes):
            raise ValueError("字节不足")

        element_bytes = param_bytes[element_start:element_end]

        if param_type == 'address':
            address_bytes = element_bytes[-20:]  # 提取最后20字节
            element = Web3.to_checksum_address(address_bytes.hex())
        else:
            element = decode([param_type], element_bytes)[0]

        elements.append(element)

    return elements, elements_start + length * 32


def parse_transaction_input(input_data, method_selector):
    """解析交易输入数据"""
    if not input_data.startswith(method_selector):
        return None

    try:
        params_hex = input_data[len(method_selector):]
        if len(params_hex) % 2 != 0:
            params_hex = '0' + params_hex  # 补齐奇数长度

        params_bytes = bytes.fromhex(params_hex)
        pos = 0

        # 解析addresses数组偏移量
        addresses_offset = decode(['uint256'], params_bytes[pos:pos + 32])[0]
        pos += 32

        # 解析timestamps数组偏移量
        timestamps_offset = decode(['uint256'], params_bytes[pos:pos + 32])[0]
        pos += 32

        # 解析maxPoolId
        max_pool_id = decode(['uint8'], params_bytes[pos:pos + 32])[0]

        # 解析动态数组
        addresses, _ = decode_dynamic_array(params_bytes, addresses_offset, 'address')
        timestamps, _ = decode_dynamic_array(params_bytes, timestamps_offset, 'uint256')

        return {
            'addresses': addresses,
            'timestamps': timestamps,
            'pool_id': max_pool_id
        }
    except Exception as e:
        print(f"解码失败: {str(e)}")
        return None


# ******************** 通知功能 ********************
def format_addresses(address_list):
    """格式化地址显示"""
    return '\n'.join([f"- `{addr[:6]}...{addr[-4:]}`" for addr in address_list[:3]]) + \
        ("\n- ..." if len(address_list) > 3 else "")


def send_dingding_alert(tx_hash, data):
    """发送钉钉通知"""
    tx_url = f"https://bscscan.com/tx/{tx_hash}"

    start_ts = data['timestamps'][0] if len(data['timestamps']) > 0 else 0
    end_ts = data['timestamps'][1] if len(data['timestamps']) > 1 else 0

    markdown = {
        "title": "🚨 检测到新IDO创建",
        "text": f"""### 🚨 检测到新IDO创建
**交易哈希**: [{tx_hash[:8]}]({tx_url})  
**池ID**: #{data['pool_id']}  
**参与地址**:  
{format_addresses(data['addresses'])}  
**时间范围**:  
`{datetime.utcfromtimestamp(start_ts)}` ➔ `{datetime.utcfromtimestamp(end_ts)}` UTC"""
    }

    try:
        response = requests.post(DINGDING_WEBHOOK,
                                 json={"msgtype": "markdown", "markdown": markdown},
                                 timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"钉钉通知异常: {str(e)}")
        return False


# ******************** 监控逻辑 ********************
def check_address(config):
    """检查单个地址的交易"""
    address = config['address']
    print(f"\n检查地址 {address}...")

    try:
        transactions = get_transactions(address)
        new_txs = []

        for tx in transactions:
            tx_hash = tx['hash']

            if tx_hash in processed_txs:
                continue

            if config['check_success'] and tx.get('isError', '1') != '0':
                continue

            parsed = parse_transaction_input(tx.get('input', ''), config['method_selector'])
            if parsed:
                new_txs.append((tx_hash, parsed))

        # 批量处理新交易
        for tx_hash, parsed in new_txs:
            if send_dingding_alert(tx_hash, parsed):
                processed_txs.add(tx_hash)
                print(f"✅ 发现新交易: {tx_hash}")

        # 保存到文件
        if new_txs:
            save_processed_txs()

    except Exception as e:
        print(f"检查地址 {address} 时发生异常: {str(e)}")


def monitoring_job():
    """定时监控任务"""
    print(f"\n⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    prev_count = len(processed_txs)

    for config in MONITOR_CONFIGS:
        check_address(config)

    new_count = len(processed_txs) - prev_count
    print(f"📊 发现 {new_count} 条新交易" if new_count > 0 else "📭 没有新交易")
    print("━" * 40)


# ******************** 主程序 ********************
if __name__ == "__main__":
    try:
        print("🚀 启动BSC监控程序")
        print(f"已加载 {len(processed_txs)} 条历史记录")

        # 立即执行一次并设置定时任务
        monitoring_job()
        schedule.every(5).minutes.do(monitoring_job)

        while True:
            schedule.run_pending()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 中断程序")
    finally:
        save_processed_txs()
        print(f"💾 已保存 {len(processed_txs)} 条处理记录")