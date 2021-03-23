import web3
import solcx
import os

from dotenv import load_dotenv
from sys import argv

from web3.middleware import geth_poa_middleware
# inject the poa compatibility middleware to the innermost layer

dotenv_path = '.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

validators = list(set(os.environ['VALIDATORS'].split(" ")))
threshold = int(os.environ['THRESHOLD'])


def deploy_bridge(side):
    w3 = web3.Web3(web3.HTTPProvider(os.environ[side + '_RPCURL']))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    master_account = w3.eth.account.from_key(os.environ['PRIVKEY'])
    gas_price = int(os.environ[side + '_GASPRICE'])
    solc_version = "0.6.0"
    solcx.install_solc(solc_version)

    compiled_code = "deployment/ValidatorsManagement.sol:ValidatorsManagement"
    compiled_contract = solcx.compile_files('deployment/ValidatorsManagement.sol', output_values=["abi", "bin"], solc_version=solc_version)
    ABI = compiled_contract[compiled_code]['abi']
    BYTECODE = compiled_contract[compiled_code]['bin']
    contract = w3.eth.contract(abi=ABI, bytecode=BYTECODE)

    needed_gas = contract.constructor(validators, threshold).estimateGas()

    nonce = w3.eth.getTransactionCount(master_account.address)
    tx_hash = contract.constructor(validators, threshold).buildTransaction(
        {'from': master_account.address,
         'chainId': w3.eth.chain_id,
         'gas': int(w3.eth.getBlock('latest').gasLimit * 0.95),#needed_gas
         'gasPrice': gas_price,
         'nonce': nonce,
         "value": 0
         }
    )

    private_key = master_account.privateKey
    signed_txn = w3.eth.account.sign_transaction(tx_hash, private_key=private_key)
    hsh = w3.eth.sendRawTransaction(signed_txn.rawTransaction).hex()
    contract_id = w3.eth.waitForTransactionReceipt(hsh)["contractAddress"]

    if side == 'LEFT':
        print(f"#1 [LEFT] Validators Set deployed at {contract_id}")
    else:
        print(f"#3 [RIGHT] Validators Set deployed at {contract_id}")
    validator = contract_id

    compiled_code = "deployment/Bridge.sol:Bridge"
    compiled_contract = solcx.compile_files('deployment/Bridge.sol', output_values=["abi", "bin"], solc_version=solc_version)
    ABI = compiled_contract[compiled_code]['abi']
    BYTECODE = compiled_contract[compiled_code]['bin']

    contract = w3.eth.contract(abi=ABI, bytecode=BYTECODE)

    nonce = w3.eth.getTransactionCount(master_account.address)
    tx_hash = contract.constructor(validator, side == "LEFT").buildTransaction(
        {'from': master_account.address,
         'chainId': w3.eth.chain_id,
         'gas':  int(w3.eth.getBlock('latest').gasLimit * 0.95),#needed_gas
         'gasPrice': gas_price,
         'nonce': nonce,
         "value": 0
         }
    )

    private_key = master_account.privateKey
    signed_txn = w3.eth.account.sign_transaction(tx_hash, private_key=private_key)
    hsh = w3.eth.sendRawTransaction(signed_txn.rawTransaction).hex()
    AttributeDict = w3.eth.waitForTransactionReceipt(hsh)
    contract_id = AttributeDict["contractAddress"]
    blockNumber = AttributeDict['blockNumber']

    if side == 'LEFT':
        print(f"#2 [LEFT] Bridge deployed at {contract_id}")
        with open(".env", "a") as myfile:
            myfile.write("\n")
            myfile.write(f'RIGHT_ADDRESS={contract_id}')
    else:
        print(f"#4 [RIGHT] Bridge deployed at {contract_id}")
        with open(".env", "a") as myfile:
            myfile.write("\n")
            myfile.write(f'LEFT_ADDRESS={contract_id}')

    return blockNumber


l_block = deploy_bridge('LEFT')
r_block = deploy_bridge('RIGHT')
print(f'#5 [LEFT] Bridge deployed at block {l_block}' )
print(f'#6 [RIGHT] Bridge deployed at block {r_block}')
with open(".env", "a") as myfile:
    myfile.write("\n")
    myfile.write(f'LEFT_START_BLOCK={l_block}')
with open(".env", "a") as myfile:
    myfile.write("\n")
    myfile.write(f'RIGHT_START_BLOCK={r_block}')