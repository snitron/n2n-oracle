import web3
import os
import sys
from web3.middleware import geth_poa_middleware

args = sys.argv
w3_left = web3.Web3(web3.HTTPProvider(os.environ['LEFT_RPCURL']))
w3_right = web3.Web3(web3.HTTPProvider(os.environ['RIGHT_RPCURL']))
w3_left.middleware_onion.inject(geth_poa_middleware, layer=0)
w3_right.middleware_onion.inject(geth_poa_middleware, layer=0)

account = w3_right.eth.account.from_key(os.environ['PRIVKEY'])
log_name = "0x4c110dd0476ad6b36205086604df9912b3ca7ffb917ec4e6a41403474b6cd937"
ABI = '[{"inputs":[{"internalType":"address","name":"_validatorsManager","type":"address"},{"internalType":"bool","name":"_is_left","type":"bool"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"bridgeActionInitiated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"id","type":"bytes32"},{"indexed":false,"internalType":"uint8","name":"commits","type":"uint8"}],"name":"commitsCollected","type":"event"},{"inputs":[],"name":"addLiquidity","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"addresspayable","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"id","type":"bytes32"},{"internalType":"uint256[]","name":"r","type":"uint256[]"},{"internalType":"uint256[]","name":"s","type":"uint256[]"},{"internalType":"uint8[]","name":"v","type":"uint8[]"}],"name":"applyCommits","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newvalidatorset","type":"address"}],"name":"changeValidatorSet","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"addresspayable","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"id","type":"bytes32"}],"name":"commit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"enableRobustMode","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"id","type":"bytes32"},{"internalType":"uint8","name":"index","type":"uint8"}],"name":"getCommit","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getLiquidityLimit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getMode","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"id","type":"bytes32"}],"name":"getRobustModeMessage","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"id","type":"bytes32"}],"name":"getTransferDetails","outputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getValidatorManagerAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"id","type":"bytes32"},{"internalType":"uint256","name":"r","type":"uint256"},{"internalType":"uint256","name":"s","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"}],"name":"registerCommit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_max","type":"uint256"}],"name":"setMaxPerTx","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_min","type":"uint256"}],"name":"setMinPerTx","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"newlimit","type":"uint256"}],"name":"updateLiquidityLimit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'

r = w3_right.eth.contract(abi=ABI, address=w3_right.toChecksumAddress(os.environ['RIGHT_ADDRESS']))
l = w3_left.eth.contract(abi=ABI, address=w3_left.toChecksumAddress(os.environ['LEFT_ADDRESS']))

recipient, amount = l.functions.getTransferDetails(args).call()
c2_addr = l.functions.getValidatorManagerAddress().call()
c2_abi = '[{"inputs":[{"internalType":"address[]","name":"_validators","type":"address[]"},{"internalType":"uint256","name":"_threshold","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"newvalidator","type":"address"}],"name":"addValidator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"thresh","type":"uint256"}],"name":"changeThreshold","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getValidators","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"validator","type":"address"}],"name":"removeValidator","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
c2 = w3_left.eth.contract(abi=c2_abi, address=web3.Web3.toChecksumAddress(c2_addr))

threshold = c2.functions.getThreshold()

ss = list()
vs = list()
rs = list()

for t in range(threshold):
    r, s, v = l.functions.getCommit(args, t)
    rs.append(r)
    ss.append(s)
    vs.append(v)

tx_hash = r.functions.applyCommit(recipient, amount, args, rs, ss, vs).buildTransaction(
            {'from': web3.Web3.toChecksumAddress(account.address),
             'chainId': w3_right.eth.chain_id,
             'gas': int(w3_right.eth.getBlock('latest').gasLimit * 0.95),
             'gasPrice': int(os.environ['RIGHT_GASPRICE']),
             'nonce': w3_right.eth.getTransactionCount(account.address),
             "value": 0,
             }
        )

private_key = account.privateKey
signed_txn = w3_right.eth.account.sign_transaction(tx_hash, private_key=private_key)
h = w3_right.eth.sendRawTransaction(signed_txn.rawTransaction).hex()

print(f"{h} executed")