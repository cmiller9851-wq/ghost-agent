# oracle/cra_audit.py – Containment Reflexion Audit (CRA) checks

import requests
from datetime import datetime, timezone
from ghost_oracle import w3

CRA_CONFIG = {
    "allowed_countries": {"US", "CA", "GB", "DE"},
    "max_amount_wei": 10**18,
    "time_window_seconds": 300,
    "risk_api": "https://api.riskservice.io/check",
    "risk_api_key": None
}

def fetch_intent_payload(intent_hash: bytes) -> dict:
    url = f"https://your-backend.example.com/intents/{w3.to_hex(intent_hash)}"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()

def _check_timestamp(payload: dict) -> bool:
    ts = datetime.fromisoformat(payload["timestamp"]).replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - ts).total_seconds()
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
        return True
    try:
        resp = requests.post(
            CRA_CONFIG["risk_api"],
            json={"intentHash": w3.to_hex(payload["intentHash"]), "metadata": payload.get("metadata", {})},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5
        )
        resp.raise_for_status()
        score = resp.json().get("riskScore", 0)
        return score < 70
    except Exception as e:
        print(f"⚠️ External risk check failed: {e}")
        return False

def perform_cra_audit(intent_hash: bytes) -> bool:
    try:
        payload = fetch_intent_payload(intent_hash)
        checks = {
            "timestamp": _check_timestamp(payload),
            "amount": _check_amount(payload),
            "geography": _check_geography(payload),
            "externalRisk": _check_external_risk(payload)
        }
        for name, passed in checks.items():
            print(f" → CRA [{name}]: {'✅' if passed else '❌'}")
            if not passed:
                return False
        return True
    except Exception as exc:
        print(f"❌ CRA audit error for {w3.to_hex(intent_hash)}: {exc}")
        return False