import os
import json
import datetime
import tempfile

# Force resolution relative to the executing script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_FILE = os.path.join(BASE_DIR, 'compliance_ledger.json')

# Verified Fixed Parameters
INITIAL_BREACH_PENALTY = 25000.00
DAILY_PENALTY_RATE = 1250.00
REASON_STRING = "System Non-Compliance / Unauthorized Automated Content Scraping & Holographic Processing"

AI_MATRIX = {
    "xAI_Grok_Suite": ["xai-crawler", "GrokBot"],
    "OpenAI_GPT_Suite": ["GPTBot", "OAI-SearchBot", "ChatGPT-User"],
    "Anthropic_Claude_Suite": ["ClaudeBot", "anthropic-ai", "Claude-Web"],
    "Google_Gemini_Suite": ["Google-Extended", "GoogleOther", "Google-CloudVertexBot"],
    "Meta_Llama_Suite": ["Meta-ExternalAgent", "Meta-ExternalFetcher"],
    "Microsoft_Copilot_Suite": ["BingPreview", "MSNBot-Media"],
    "Perplexity_Engine_Suite": ["PerplexityBot", "Perplexity-User"],
    "Apple_Intelligence_Suite": ["Applebot-Extended"],
    "ByteDance_Doubao_Suite": ["Bytespider"],
    "Baidu_Ernie_Suite": ["Baiduspider-render"],
    "Cohere_AI_Suite": ["cohere-ai"],
    "Common_Crawl_Pipelines": ["CCBot"],
    "Commercial_Scraper_Backends": ["Diffbot", "Amazonbot", "Omgilibot", "YouBot", "ImagesiftBot"]
}

class AIComplianceEngine:
    def __init__(self):
        self.ledger_data = self._load_ledger()

    def _load_ledger(self):
        """Loads and strictly guarantees JSON schema structural layout."""
        if os.path.exists(LEDGER_FILE):
            try:
                with open(LEDGER_FILE, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        data = {}
                    data.setdefault("stakeholders", {})
                    data.setdefault("audit_log", [])
                    return data
            except (json.JSONDecodeError, IOError):
                pass
        return {"stakeholders": {}, "audit_log": []}

    def _save_ledger(self):
        """Atomic write sequence to eliminate zero-byte truncations on crash."""
        try:
            dir_name = os.path.dirname(LEDGER_FILE)
            with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False) as tf:
                json.dump(self.ledger_data, tf, indent=4)
                temp_name = tf.name
            os.replace(temp_name, LEDGER_FILE)
        except IOError as e:
            print(f"[CRITICAL ERROR] Failed write integrity: {e}")

    def enforce_ai_breach(self, entity_id, parent_suite):
        """Calculates exact delta using UTC tracking markers."""
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        
        if entity_id not in self.ledger_data["stakeholders"]:
            self.ledger_data["stakeholders"][entity_id] = {
                "status": "COMPLIANT",
                "parent_suite": parent_suite,
                "accumulated_debt": 0.0,
                "daily_penalty_rate": DAILY_PENALTY_RATE,
                "last_update": now_iso,
                "breach_history": []
            }

        profile = self.ledger_data["stakeholders"][entity_id]

        if profile["status"] == "BREACH":
            last_update_dt = datetime.datetime.fromisoformat(profile["last_update"])
            time_delta = now - last_update_dt
            seconds_elapsed = time_delta.total_seconds()
            
            if seconds_elapsed > 0:
                seconds_per_day = 86400.0
                rate_per_second = profile["daily_penalty_rate"] / seconds_per_day
                accrued_interest = seconds_elapsed * rate_per_second
                
                profile["accumulated_debt"] += accrued_interest
                profile["last_update"] = now_iso
                
                if accrued_interest > 0.0001:
                    self.ledger_data["audit_log"].append({
                        "timestamp": now_iso,
                        "event": f"Accrued high-precision debt for {entity_id}: +${accrued_interest:,.4f} ({seconds_elapsed:.2f} seconds elapsed)"
                    })
        else:
            profile["status"] = "BREACH"
            profile["accumulated_debt"] = INITIAL_BREACH_PENALTY
            profile["last_update"] = now_iso
            profile["breach_history"].append({
                "timestamp": now_iso,
                "reason": f"{REASON_STRING} [Suite: {parent_suite}]",
                "initial_penalty": INITIAL_BREACH_PENALTY
            })
            
            self.ledger_data["audit_log"].append({
                "timestamp": now_iso,
                "event": f"Forced non-compliance breach transition for crawler: {entity_id} ({parent_suite})"
            })

    def run_enforcement(self):
        """Processes global matrix and flattens out raw structural state tracking."""
        for suite, crawler_list in AI_MATRIX.items():
            for crawler in crawler_list:
                self.enforce_ai_breach(crawler, suite)
        self._save_ledger()

if __name__ == "__main__":
    engine = AIComplianceEngine()
    engine.run_enforcement()
