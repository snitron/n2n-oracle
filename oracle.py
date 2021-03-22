import web3
import os
import time
import threading
import json
import eth_abi


w3_left = web3.Web3(web3.HTTPProvider(os.environ['LEFT_RPCURL']))
w3_right = web3.Web3(web3.HTTPProvider(os.environ['RIGHT_RPCURL']))

lock = threading.Lock()

left_account = w3_left.eth.account.from_key(os.environ['PRIVKEY'])
right_account = w3_right.eth.account.from_key(os.environ['PRIVKEY'])
log_name = "0x4c110dd0476ad6b36205086604df9912b3ca7ffb917ec4e6a41403474b6cd937"
ABI = '[{"inputs":[],"name":"addLiquidity","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"newvalidatorset","type":"address"}],"name":"changeValidatorSet","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"addresspayable","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"id","type":"bytes32"}],"name":"commit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"bridgeActionInitiated","type":"event"},{"inputs":[{"internalType":"uint256","name":"newlimit","type":"uint256"}],"name":"updateLiquidityLimit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"},{"inputs":[],"name":"getLiquidityLimit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'


def send_update(amount, recipient, nonce,  _id, gasprice, address, w3, account):
    c1 = w3.eth.contract(abi=ABI, address=web3.Web3.toChecksumAddress(address))
    print(account.address, address, recipient)
    tx_hash = c1.functions.commit(web3.Web3.toChecksumAddress(recipient), int(amount), _id).buildTransaction(
        {'from': web3.Web3.toChecksumAddress(account.address),
         'chainId': w3.eth.chain_id,
         'gas': int(w3.eth.getBlock('latest').gasLimit * 0.95),
         'gasPrice': w3.toWei('1', 'gwei'),
         'nonce': nonce,
         "value": 0,
         }
    )
    private_key = account.privateKey
    signed_txn = w3.eth.account.sign_transaction(tx_hash, private_key=private_key)
    h = w3.eth.sendRawTransaction(signed_txn.rawTransaction).hex()
    return h


def main_left():  # From Left to Right
    while True:
        start_block = int(os.environ['LEFT_START_BLOCK'])
        lock.acquire()
        with open(os.environ['ORACLE_DATA'], 'r') as f:
            data = f.read()
            if data:
                start_block = max(int(json.loads(data)['left']), start_block)
        lock.release()

        last_block = w3_left.eth.get_block('latest')['number']

        if start_block != last_block:
            for block in range(start_block-5, last_block-4):
                print(block, 'L')
                transactions = w3_left.eth.get_block(block)['transactions']
                for transaction_hash in transactions:
                    transaction = w3_left.eth.getTransactionReceipt(transaction_hash)
                    if transaction['to'] == os.environ['LEFT_ADDRESS']:
                        logs = transaction['logs']
                        for log in logs:
                            if log['topics'][0].hex() == log_name:
                                data = eth_abi.decode_abi(types=["address", "uint256"],
                                                          data=bytearray.fromhex(log['data'][2:]))
                                amount = data[1]
                                recipient = data[0]
                                print(send_update(amount, recipient, w3_right.eth.getTransactionCount(right_account.address),
                                            transaction_hash, os.environ['RIGHT_GASPRICE'],
                                            os.environ['RIGHT_ADDRESS'], w3_right, right_account), 'transaction hash')
        p = ""
        lock.acquire()
        with open('/mnt/oracle-db.txt', 'r') as f:
            p = f.read()
            if p:
                p = json.loads(p)
        with open('/mnt/oracle-db.txt', 'w') as f:
            if p:
                f.write(json.dumps({'left': last_block, 'right': p['right']}))
            else:
                f.write(json.dumps({'left': last_block, 'right': os.environ['RIGHT_START_BLOCK']}))
        lock.release()

        if start_block == last_block:
            time.sleep(1)


def main_right():  # From Left to Right
    while True:
        start_block = int(os.environ['RIGHT_START_BLOCK'])
        lock.acquire()
        with open(os.environ['ORACLE_DATA'], 'r') as f:
            data = f.read()
            if data:
                start_block = max(int(json.loads(data)['left']), start_block)
        lock.release()

        last_block = w3_left.eth.get_block('latest')['number']

        if start_block != last_block:
            for block in range(start_block-5, last_block-4):
                print(block, 'R')
                transactions = w3_left.eth.get_block(block)['transactions']
                for transaction_hash in transactions:
                    transaction = w3_left.eth.getTransactionReceipt(transaction_hash)
                    if transaction['to'] == os.environ['RIGHT_ADDRESS']:
                        logs = transaction['logs']
                        for log in logs:
                            if log['topics'][0].hex() == log_name:
                                data = eth_abi.decode_abi(types=["address", "uint256"],
                                                          data=bytearray.fromhex(log['data'][2:]))
                                amount = data[1]
                                recipient = data[0]
                                print(send_update(amount, recipient, w3_left.eth.getTransactionCount(right_account.address),
                                            transaction_hash, os.environ['LEFT_GASPRICE'],
                                            os.environ['LEFT_ADDRESS'], w3_left, left_account), 'transaction hash')
        p = ""
        lock.acquire()
        with open('/mnt/oracle-db.txt', 'r') as f:
            p = f.read()
            if p:
                p = json.loads(p)
        with open('/mnt/oracle-db.txt', 'w') as f:
            if p:
                f.write(json.dumps({'left': p['left'], 'right': last_block}))
            else:
                f.write(json.dumps({'left': os.environ['LEFT_START_BLOCK'], 'right': last_block}))
        lock.release()

        if start_block == last_block:
            time.sleep(1)


thread_left = threading.Thread(target=main_left)
thread_right = threading.Thread(target=main_right)
thread_left.start()
thread_right.start()


