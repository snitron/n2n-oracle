import threading
import json
import eth_abi
import os
from threading import Thread
import time
import web3
import time
from web3.middleware import geth_poa_middleware

import logging

logging.basicConfig(level=logging.INFO)

logging.info('Here to stderr')



l_start = int(os.environ['LEFT_START_BLOCK'])
r_start = int(os.environ['RIGHT_START_BLOCK'])

print(os.system(f"cd {os.environ['ORACLE_DATA']} ; ls -l"))
os.environ['ORACLE_DATA'] = "/mountedcum/cum.json"
print(os.system(f"cd /mountedcum ; ls -l"))
print("test", os.environ['ORACLE_DATA'])

if not os.path.exists(os.environ['ORACLE_DATA']):
    print("cum")
    with open(os.environ['ORACLE_DATA'], 'w') as f:
        f.write(json.dumps({'left': os.environ['LEFT_START_BLOCK'], 'right': os.environ['RIGHT_START_BLOCK']}))
        f.flush()


with open(os.environ['ORACLE_DATA'], 'r') as f:
    data = f.read()
    if data:
        os.environ['LEFT_START_BLOCK'] = str(max(int(json.loads(data)['left']), l_start))

with open(os.environ['ORACLE_DATA'], 'r') as f:
    data = f.read()
    if data:
        os.environ['RIGHT_START_BLOCK'] = str(max(int(json.loads(data)['right']), r_start))

w3_left = web3.Web3(web3.HTTPProvider(os.environ['LEFT_RPCURL']))
w3_right = web3.Web3(web3.HTTPProvider(os.environ['RIGHT_RPCURL']))
w3_left.middleware_onion.inject(geth_poa_middleware, layer=0)
w3_right.middleware_onion.inject(geth_poa_middleware, layer=0)

left_account = w3_left.eth.account.from_key(os.environ['PRIVKEY'])
right_account = w3_right.eth.account.from_key(os.environ['PRIVKEY'])

ABI = '[{"inputs":[{"internalType":"address","name":"_validatorsManager","type":"address"},{"internalType":"bool","name":"_is_left","type":"bool"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"bridgeActionInitiated","type":"event"},{"inputs":[],"name":"addLiquidity","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"newvalidatorset","type":"address"}],"name":"changeValidatorSet","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"addresspayable","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"id","type":"bytes32"}],"name":"commit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getLiquidityLimit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getValidatorManagerAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"newlimit","type":"uint256"}],"name":"updateLiquidityLimit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'
r = w3_right.eth.contract(abi=ABI, address=w3_right.toChecksumAddress(os.environ['RIGHT_ADDRESS']))
l = w3_left.eth.contract(abi=ABI, address=w3_left.toChecksumAddress(os.environ['LEFT_ADDRESS']))

r_filter = r.events.bridgeActionInitiated.createFilter(fromBlock=hex(int(os.environ['RIGHT_START_BLOCK'])))
l_filter = l.events.bridgeActionInitiated.createFilter(fromBlock=hex(int(os.environ['LEFT_START_BLOCK'])))


def send_update(amount, recipient, nonce, _id, gasprice, address, w3, account):
    c1 = w3.eth.contract(abi=ABI, address=web3.Web3.toChecksumAddress(address))
    c2_addr = c1.functions.getValidatorManagerAddress().call()
    c2_abi = '[{"inputs":[{"internalType":"address[]","name":"_validators","type":"address[]"},{"internalType":"uint256","name":"_threshold","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"newvalidator","type":"address"}],"name":"addValidator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"thresh","type":"uint256"}],"name":"changeThreshold","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getValidators","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"validator","type":"address"}],"name":"removeValidator","outputs":[],"stateMutability":"nonpayable","type":"function"}]'

    c2 = w3.eth.contract(abi=c2_abi, address=web3.Web3.toChecksumAddress(c2_addr))
    validators = c2.functions.getValidators().call()
    ############
    while account.address not in validators:
        time.sleep(5)
        validators = c2.functions.getValidators().call()

    if account.address in validators:
        print(account.address, address, recipient)
        tx_hash = c1.functions.commit(web3.Web3.toChecksumAddress(recipient), amount, _id).buildTransaction(
            {'from': web3.Web3.toChecksumAddress(account.address),
             'chainId': w3.eth.chain_id,
             'gas': int(w3.eth.getBlock('latest').gasLimit * 0.95),
             'gasPrice': int(gasprice),
             'nonce': nonce,
             "value": 0,
             }
        )
        private_key = account.privateKey
        signed_txn = w3.eth.account.sign_transaction(tx_hash, private_key=private_key)
        h = w3.eth.sendRawTransaction(signed_txn.rawTransaction).hex()
        return h
log = None
for log in r_filter.get_all_entries():
    args = log['args']
    amount = args['amount']
    recipient = args['recipient']
    txh = log['transactionHash']
    hsh = send_update(amount, recipient, w3_left.eth.getTransactionCount(left_account.address),
                      txh, os.environ['LEFT_GASPRICE'], os.environ['LEFT_ADDRESS'],
                      w3_left, left_account)
    print(hsh)

if log:
    r_last = log['blockNumber']
else:
    r_last = w3_right.eth.get_block('latest')['number']
os.environ['RIGHT_START_BLOCK'] = str(r_last)

log = None
for log in l_filter.get_all_entries():
    args = log['args']
    amount = args['amount']
    recipient = args['recipient']
    txh = log['transactionHash']
    hsh = send_update(amount, recipient, w3_right.eth.getTransactionCount(right_account.address),
                      txh, os.environ['RIGHT_GASPRICE'], os.environ['RIGHT_ADDRESS'],
                      w3_right, right_account)
    print(hsh)

if log:
    l_last = log['blockNumber']
else:
    l_last = w3_left.eth.get_block('latest')['number']
os.environ['LEFT_START_BLOCK'] = str(l_last)

lock = threading.Lock()


def log_loop_left(event_filter, poll_interval):
    while True:
        print("l")
        for log_l in event_filter.get_new_entries():
            print("dasd")
            args = log_l['args']
            amount = args['amount']
            recipient = args['recipient']
            txh = log_l['transactionHash']

            hsh = send_update(amount, recipient, w3_right.eth.getTransactionCount(right_account.address),
                              txh, os.environ['RIGHT_GASPRICE'], os.environ['RIGHT_ADDRESS'],
                              w3_right, right_account)
        os.environ['LEFT_START_BLOCK'] = str(w3_left.eth.get_block('latest')['number'])

        time.sleep(poll_interval)


def log_loop_right(event_filter, poll_interval):
    while True:
        print("r")
        for log_r in event_filter.get_new_entries():
            args = log_r['args']
            amount = args['amount']
            recipient = args['recipient']
            txh = log_r['transactionHash']

            hsh = send_update(amount, recipient, w3_left.eth.getTransactionCount(left_account.address),
                              txh, os.environ['LEFT_GASPRICE'], os.environ['LEFT_ADDRESS'],
                              w3_left, left_account)

        os.environ['RIGHT_START_BLOCK'] = str(w3_right.eth.get_block('latest')['number'])

        time.sleep(poll_interval)


thread_left = threading.Thread(target=log_loop_left, args=(l_filter, 1))
thread_right = threading.Thread(target=log_loop_right, args=(r_filter, 1))
thread_left.start()
thread_right.start()

while True:
    print("q")
    f = open(os.environ['ORACLE_DATA'], 'w')
    f.write(json.dumps({'left': os.environ['LEFT_START_BLOCK'], 'right': os.environ['RIGHT_START_BLOCK']}))
    time.sleep(1)
