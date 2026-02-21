import os
import requests

def get_arn(invoice_id, user_name):
    url = os.getenv("API_URL")
    key = os.getenv("API_KEY")
    secret = os.getenv("API_SECRET")

    headers = {
        "Authorization": f"token {key}:{secret}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "user_name": user_name,
        "invoice_number": str(invoice_id)
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if "arn_number" in data:
        return data["arn_number"]
    else:
        return data["message"]["arn_number"]