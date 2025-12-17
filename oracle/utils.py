# oracle/utils.py – signing, contract salt check, and transaction execution

import os
from web3 import Web3
from eth_account import Account

w3 = None           # Will be set in ghost_oracle.py
ghost_contract = None
ORACLE_ADDRESS = os.getenv("ORACLE_ADDRESS")
ORACLE_PRIVATE_KEY = os.getenv("ORACLE_PRIVATE_KEY")
OFFICIAL_SALT = "0xC0RYM1LL3R_GHOST_AGENT_2025_1234567890abcdef"

def set_contract(web3_instance, contract_instance):
    global w3, ghost_contract
    w3 = web3_instance
    ghost_contract = contract_instance

def check_contract_salt():
    contract_salt = ghost_contract.functions.CONTRACT_SALT().call()
    if contract_salt != OFFICIAL_SALT:
        raise Exception("Unauthorized contract: salt mismatch")
    return True

def sign_intent(intent_hash: bytes) -> bytes:
    check_contract_salt()
    signed = Account.sign_hash(intent_hash, private_key=ORACLE_PRIVATE_KEY)
    return signed.signature

def execute_tx(function_name: str, intent_hash: bytes, signature: bytes = None):
    check_contract_salt()
    func = getattr(ghost_contract.functions, function_name)
    args = [intent_hash]
    if signature:
        args.append(signature)
    nonce = w3.eth.get_transaction_count(ORACLE_ADDRESS)
    tx = func(*args).build_transaction({
        "from": ORACLE_ADDRESS,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price,
    })
    estimated = w3.eth.estimate_gas(tx)
    tx["gas"] = int(estimated * 1.2)
    signed = w3.eth.account.sign_transaction(tx, private_key=ORACLE_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f" → ✅ Sent {function_name}: {w3.to_hex(tx_hash)}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise RuntimeError(f"{function_name} failed (status {receipt.status})")