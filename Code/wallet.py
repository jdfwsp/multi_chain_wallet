# Import dependencies
import bit
from bit.network import NetworkAPI
import lit
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import subprocess
import json
import os
from dotenv import load_dotenv
from constants import *

# Loads and sets environment variables
load_dotenv()
mnemonic=os.getenv("mnemonic")

# Connects to private ETH POA blockchain
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8181'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

help = '''
Usage:
send_tx(ETH, coins[ETH][0]['privkey'], coins[ETH][2]['address'], Web3.toWei(1, 'ether'))
send_tx(BTCTEST, coins[BTCTEST][0]['privkey'], coins[BTCTEST][2]['address'], .0001)
'''
 
# Derives wallet addresses from provided mnemonic for specified coins
def derive_wallets(coin):
    cols = 'address,index,path,privkey,pubkey,pubkeyhash,xprv,xpub'
    command = f'derive --mnemonic=mnemonic --cols={cols} --coin={coin} --numderive=3 --format=json -g'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    return json.loads(output) 

# Creates a dictionary object to store the output from `derive_wallets`
coins = {BTCTEST: derive_wallets(BTCTEST), ETH: derive_wallets(ETH)}

# Checks which coin then returns address from supplied private key
def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    elif coin == BTCTEST:
        return bit.PrivateKeyTestnet(priv_key)

# Creates an unsigned transaction appropriate metadata
def create_tx(coin, account, recipient, amount):
    if coin == ETH:
        account = priv_key_to_account(coin, account)
        gasEstimate = w3.eth.estimateGas(
            {"from": account.address, "to": recipient, "value": amount}
        )
        return {
            "chainId": 888,
            "from": account.address,
            "to": recipient,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address),
        }, account
    elif coin == BTCTEST:
        account = priv_key_to_account(coin, account)
        return bit.PrivateKeyTestnet.prepare_transaction(account.address, [(recipient, amount, BTC)]), account

# Signs and sends the transaction
def send_tx(coin, account, recipient, amount):
    tx, account = create_tx(coin, account, recipient, amount)
    signed_tx = account.sign_transaction(tx)
    if coin == ETH:
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return result
    elif coin == BTCTEST:
        result = NetworkAPI.broadcast_tx_testnet(signed_tx)
        return result
