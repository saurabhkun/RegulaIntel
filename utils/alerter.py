import os
import requests

def send_slack_alert(severity: str, message: str):
    """
    Simulates sending an active autonomous alert webhook to a compliance channel.
    Crucial 'X-Factor' showing that the multi-agent system doesn't just draft, 
    but proactively reaches out.
    """
    payload = {
        "text": f"🚨 *{severity} REGULATORY DETECTED* 🚨\n{message}\n\nPlease review the RegulaIntel Dashboard immediately."
    }
    
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if webhook_url:
        try:
            requests.post(webhook_url, json=payload, timeout=3)
            return f"Published to Slack: {webhook_url}"
        except Exception as e:
            pass
            
    # Dev/Mock fallback
    return payload
