# --------------------------------------------------------------
# ghost_oracle.py – Python Oracle for the GhostAgent contract
# --------------------------------------------------------------

import os
import sys
import time
import requests
from typing import Optional, List

from web3 import Web3
from eth_account import Account
from apscheduler.schedulers.background import BackgroundScheduler

# --------------------------------------------------------------
# 1️⃣ Configuration – load from environment variables
# --------------------------------------------------------------
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
ORACLE_PRIVATE_KEY = os.getenv("ORACLE_PRIVATE_KEY")
ORACLE_ADDRESS = os.getenv("ORACLE_ADDRESS")

# Minimal ABI – only the functions/events we need
GHOST_AGENT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "intentHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "declarer", "type": "address"},
        ],
        "name": "IntentDeclared",
        "type": "event",
    },
    "function verifyIntent(bytes32 _intentHash, bytes _signature)",
    "function seizeAssets(bytes32 _intentHash)",
    "function intents(bytes32) view returns (address declarer, bytes32 intentHash, uint8 status)",
]

# --------------------------------------------------------------
# 2️⃣ Web3 setup
# --------------------------------------------------------------
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print("🚨 Cannot connect to RPC", file=sys.stderr)
    sys.exit(1)

if not all([CONTRACT_ADDRESS, ORACLE_PRIVATE_KEY, ORACLE_ADDRESS]):
    print(
        "🛑 Set CONTRACT_ADDRESS, ORACLE_PRIVATE_KEY, and ORACLE_ADDRESS in the environment",
        file=sys.stderr,
    )
    sys.exit(1)

ghost_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=GHOST_AGENT_ABI)

print(f"✅ Connected to chain {w3.eth.chain_id}, contract at {CONTRACT_ADDRESS}")

# --------------------------------------------------------------
# 3️⃣ CRA Protocol – audit logic (simplified but ready to extend)
# --------------------------------------------------------------
CRA_CONFIG = {
    "allowed_countries": {"US", "CA", "GB", "DE"},
    "max_amount_wei": 10**18,  # 1 ETH demo limit
    "time_window_seconds": 300,
    "risk_api": "https://api.riskservice.io/check",
    "risk_api_key": os.getenv("RISK_API_KEY", ""),
}


def fetch_intent_payload(intent_hash: bytes) -> dict:
    """
    Pull the original intent payload from your off‑chain store.
    Replace the URL with your real backend endpoint.
    """
    url = f"https://your-backend.example.com/intents/{w3.to_hex(intent_hash)}"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()


def _check_timestamp(payload: dict) -> bool:
    ts = int(payload.get("timestamp", 0))
    age = time.time() - ts
    return age <= CRA_CONFIG["time_window_seconds"]


def _check_amount(payload: dict) -> bool:
    amount = int(payload.get("amountWei", 0))
    return amount <= CRA_CONFIG["max_amount_wei"]


def _check_geography(payload: dict) -> bool:
    country = payload.get("originCountry", "").upper()
    return country in CRA_CONFIG["allowed_countries"]


def _check_external_risk(payload: dict) -> bool:
    api_key = CRA_CONFIG["risk_api_key"]
    if not api_key:
        return True  # skip if you have no external service
    try:
        r = requests.post(
            CRA_CONFIG["risk_api"],
            json={"intentHash": w3.to_hex(payload["intentHash"]), "metadata": payload.get("metadata", {})},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5,
        )
        r.raise_for_status()
        score = r.json().get("riskScore", 0)
        return score < 70
    except Exception as e:
        print(f"⚠️ External risk check failed: {e}", file=sys.stderr)
        return False


def perform_cra_audit(intent_hash: bytes) -> bool:
    """Run all CRA checks; return True only if every check passes."""
    try:
        payload = fetch_intent_payload(intent_hash)

        checks = {
            "timestamp": _check_timestamp(payload),
            "amount": _check_amount(payload),
            "geography": _check_geography(payload),
            "externalRisk": _check_external_risk(payload),
        }

        for name, ok in checks.items():
            print(f"  → CRA [{name}]: {'✅' if ok else '❌'}")
            if not ok:
                return False
        return True
    except Exception as exc:
        print(f"❌ CRA audit error for {w3.to_hex(intent_hash)}: {exc}", file=sys.stderr)
        return False


# --------------------------------------------------------------
# 4️⃣ Helper – sign the intent hash with the Oracle’s private key
# --------------------------------------------------------------
def sign_intent(intent_hash: bytes) -> bytes:
    """
    Returns a 65‑byte ECDSA signature (r‖s‖v) for the given intent hash.
    The contract will apply the Ethereum message prefix internally.
    """
    signed = Account.sign_hash(intent_hash, private_key=ORACLE_PRIVATE_KEY)
    return signed.signature


# --------------------------------------------------------------
# 5️⃣ Transaction executor (build → estimate → sign → send)
# --------------------------------------------------------------
def execute_tx(function_name: str, intent_hash: bytes, signature: Optional[bytes] = None):
    func = getattr(ghost_contract.functions, function_name)
    args = [intent_hash]
    if signature is not None:
        args.append(signature)

    nonce = w3.eth.get_transaction_count(ORACLE_ADDRESS)

    # Build the transaction dict
    tx = func(*args).build_transaction(
        {
            "from": ORACLE_ADDRESS,
            "nonce": nonce,
            "gasPrice": w3.eth.gas_price,
        }
    )

    # Estimate gas and add a 20 % safety margin
    estimated = w3.eth.estimate_gas(tx)
    tx["gas"] = int(estimated * 1.2)

    # Sign & send
    signed = w3.eth.account.sign_transaction(tx, private_key=ORACLE_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"  → ✅ Sent {function_name}: {w3.to_hex(tx_hash)}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise RuntimeError(f"{function_name} failed (status {receipt.status})")
    print(f"  → ✅ {function_name} mined, gas used: {receipt.gasUsed}")


# --------------------------------------------------------------
# 6️⃣ Event handling
# --------------------------------------------------------------
processed = set()


def handle_intent(event):
    intent_hash = event["args"]["intentHash"]
    if intent_hash in processed:
        return

    print(f"\n📢 New IntentDeclared – {w3.to_hex(intent_hash)}")

    if not perform_cra_audit(intent_hash):
        print("  → ❌ CRA audit failed – intent will not be verified.")
        processed.add(intent_hash)
        return

    # CRA passed → sign and move through the contract
    sig = sign_intent(intent_hash)

    try:
        execute_tx("verifyIntent", intent_hash, sig)
        execute_tx("seizeAssets", intent_hash)
    except Exception as exc:
        print(f"  → ❌ Execution error: {exc}", file=sys.stderr)

    processed.add(intent_hash)


# --------------------------------------------------------------
# 7️⃣ Scheduler – poll for new IntentDeclared events every 5 s
# --------------------------------------------------------------
def monitor_job():
    try:
        # Create a filter that starts at the latest block each run
        flt = ghost_contract.events.IntentDeclared.create_filter(fromBlock="latest")
        for ev in flt.get_new_entries():
            handle_intent(ev)
    except Exception as exc:
        print(f"⚠️ Monitoring error: {exc}", file=sys.stderr)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(monitor_job, "interval", seconds=5, max_instances=1)
    scheduler.start()
    print("✅ Scheduler started – checking for IntentDeclared every 5 s")
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("🛑 Scheduler stopped.")


if __name__ == "__main__":
    start_scheduler()
