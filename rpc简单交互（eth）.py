import requests
from web3 import Web3
import sys
import time


class TestnetETHClient:
    def __init__(self, rpc_url):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("无法连接到RPC节点")
        self.rpc_url = rpc_url

    def get_balance(self, address):
        """查询的ETH余额，所以单位是eth"""
        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance_wei, 'ether')

    def get_nonce(self, address):
        """获取最新的nonce"""
        return self.w3.eth.get_transaction_count(address, 'pending')

    def send_eth_transaction(self, from_privkey, to_address, amount_eth):
        """发送ETH交易"""
        # 验证地址格式（以免格式错误，方便核对）
        if not Web3.is_address(to_address):
            raise ValueError("无效的接收地址")

        # 获取账户的信息
        account = self.w3.eth.account.from_key(from_privkey)
        from_address = account.address

        # 获取链的信息
        chain_id = self.w3.eth.chain_id
        nonce = self.get_nonce(from_address)
        gas_price = self.w3.eth.gas_price

        # 构建交易
        tx = {
            'from': from_address,
            'to': Web3.to_checksum_address(to_address),
            'value': self.w3.to_wei(amount_eth, 'ether'),
            'gas': 21000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': chain_id
        }

        # 估算Gas（手续费，简单场景使用固定值，具体实际交易再看情况）
        try:
            estimated_gas = self.w3.eth.estimate_gas(tx)
            tx['gas'] = estimated_gas
        except:
            pass

        # 检查余额是否足够
        balance = self.get_balance(from_address)
        required = amount_eth + (tx['gas'] * gas_price) / 1e18
        if balance < required:
            raise ValueError(f"余额不足，需要至少 {required:.6f} ETH")

        # 签名并发送交易
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def wait_for_transaction(self, tx_hash, timeout=120):
        """等待交易确认的"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt and receipt["blockNumber"]:
                    return True
            except:
                pass
            time.sleep(5)
        return False


def input_private_key():
    """安全输入私钥"""
    return input("输入发送方私钥：")


def main():
    # 配置测试网RPC（在这里用Sepolia，因为我领的是测试代币）
    RPC_URL = "https://sepolia.b3.fun"

    # 初始化客户端
    try:
        client = TestnetETHClient(RPC_URL)
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        sys.exit(1)

    # 账户的信息
    account1_priv = input_private_key()
    account1_addr = Web3.to_checksum_address("0xd9Fc4bfaE200e7Ed24071bE719a59565fef5E8Ad")
    account2_addr = Web3.to_checksum_address("0x8C6907Da783fB14c32803fdA7C4edC1D18E6a09D")

    try:
        # 查询初始余额
        print("\n【初始余额】")
        balance1 = client.get_balance(account1_addr)
        balance2 = client.get_balance(account2_addr)
        print(f"账户1余额: {balance1:.6f} ETH")
        print(f"账户2余额: {balance2:.6f} ETH")

        # 输入转账金额
        while True:
            try:
                amount = float(input("\n请输入转账金额（ETH）: "))
                if amount <= 0:
                    print("金额必须大于0")
                    continue
                break
            except ValueError:
                print("请输入有效数字")

        # 获取当前nonce
        current_nonce = client.get_nonce(account1_addr)
        print(f"\n当前Nonce: {current_nonce}")

        # 发送交易
        print("\n正在发送交易...")
        tx_hash = client.send_eth_transaction(account1_priv, account2_addr, amount)
        print(f"交易哈希: {tx_hash}")

        # 等待确认
        print("等待交易确认...（最多等待2分钟）")
        if client.wait_for_transaction(tx_hash):
            print("交易已确认！")
        else:
            print("交易确认超时，请检查区块链浏览器")

        # 查询最终余额
        print("\n【最终余额】")
        new_balance1 = client.get_balance(account1_addr)
        new_balance2 = client.get_balance(account2_addr)
        print(f"账户1余额: {new_balance1:.6f} ETH")
        print(f"账户2余额: {new_balance2:.6f} ETH")

    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()