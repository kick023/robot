import requests
from web3 import Web3
import sys
import time

# 在TestnetETHClient类中添加以下内容
class TestnetETHClient:
    def __init__(self, rpc_url):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("无法连接到RPC节点")
        self.rpc_url = rpc_url

        # 添加USDC合约配置（Sepolia测试网里给的示例）
        self.usdc_contract_address = Web3.to_checksum_address("0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238")
        self.usdc_abi = [{
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }, {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }, {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }]


    def get_usdc_balance(self, address):
        """查询USDC余额（单位：完整代币）"""
        contract = self.w3.eth.contract(
            address=self.usdc_contract_address,
            abi=self.usdc_abi
        )

        try:
            decimals = contract.functions.decimals().call()
            balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
            return balance / (10 ** decimals)
        except Exception as e:
            raise ValueError(f"USDC余额查询失败: {str(e)}")

    def get_balance(self, address):
        """查询ETH余额（单位：ETH）"""
        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance_wei, 'ether')

    def send_usdc_transaction(self, from_privkey, to_address, amount_usdc):
        """发送USDC交易"""
        # 验证地址格式
        if not Web3.is_address(to_address):
            raise ValueError("无效的接收地址")

        # 获取账户信息
        account = self.w3.eth.account.from_key(from_privkey)
        from_address = account.address

        # 初始化合约
        contract = self.w3.eth.contract(
            address=self.usdc_contract_address,
            abi=self.usdc_abi
        )

        # 获取代币精度
        decimals = contract.functions.decimals().call()
        amount = int(amount_usdc * (10 ** decimals))

        # 检查USDC余额
        balance = contract.functions.balanceOf(from_address).call()
        if balance < amount:
            raise ValueError(f"USDC余额不足，需要至少 {amount_usdc} USDC")

        # 构建交易
        tx = contract.functions.transfer(
            Web3.to_checksum_address(to_address),
            amount
        ).build_transaction({
            'from': from_address,
            'chainId': self.w3.eth.chain_id,
            'gas': 50000,  # ERC20转账一般可能需要更多gas
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(from_address, 'pending')
        })

        # 自动估算gas（可以不用）
        try:
            tx['gas'] = self.w3.eth.estimate_gas(tx)
        except:
            pass

        # 签名并发送交易
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()


    def wait_for_transaction(self, tx_hash, timeout=120):
        """等待交易确认"""
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

# 修改main函数中的余额查询部分
def main():
    # 配置测试网RPC（Sepolia示例）
    RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
    # 初始化客户端
    try:
        client = TestnetETHClient(RPC_URL)
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        sys.exit(1)

    # 账户信息
    account1_priv = input_private_key()
    account1_addr = Web3.to_checksum_address("your")
    account2_addr = Web3.to_checksum_address("")

    try:
        # 查询初始余额
        print("\n【初始余额】")
        eth_balance1 = client.get_balance(account1_addr)
        usdc_balance1 = client.get_usdc_balance(account1_addr)
        usdc_balance2 = client.get_usdc_balance(account2_addr)
        print(f"账户1 ETH余额: {eth_balance1:.6f} ETH")
        print(f"账户1 USDC余额: {usdc_balance1:.6f} USDC")
        print(f"账户2 USDC余额: {usdc_balance2:.6f} USDC")

        # 输入转账金额
        while True:
            try:
                amount = float(input("\n请输入转账金额（USDC）: "))
                if amount <= 0:
                    print("金额必须大于0")
                    continue
                break
            except ValueError:
                print("请输入有效数字")

        # 发送USDC交易
        print("\n正在发送USDC交易...")
        tx_hash = client.send_usdc_transaction(account1_priv, account2_addr, amount)
        print(f"交易哈希: {tx_hash}")

        # 等待确认
        print("等待交易确认...")
        if client.wait_for_transaction(tx_hash):
            print("交易已确认！")
        else:
            print("交易确认超时，检查区块链浏览器")

        # 查询最终余额
        print("\n【最终余额】")
        new_usdc1 = client.get_usdc_balance(account1_addr)
        new_usdc2 = client.get_usdc_balance(account2_addr)
        print(f"账户1 USDC余额: {new_usdc1:.6f} USDC")
        print(f"账户2 USDC余额: {new_usdc2:.6f} USDC")

    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":

    main()