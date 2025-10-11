import os, requests
from decouple import config
from .utils import generate_signature

PAYOS_BASE_URL = "https://api-merchant.payos.vn"
PAYOS_CREATE_PATH = "/v2/payment-requests"

CLIENT_ID = config("PAYOS_CLIENT_ID")
API_KEY = config("PAYOS_API_KEY")
CHECKSUM_KEY = config("PAYOS_CHECKSUM_KEY")

def create_payment_request(order_code, amount, description, return_url, cancel_url, buyer=None):
    url = f"{PAYOS_BASE_URL}{PAYOS_CREATE_PATH}"
    headers = {
        "x-client-id": CLIENT_ID,
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    signature = generate_signature(order_code, amount, description, return_url, cancel_url, CHECKSUM_KEY)

    body = {
        "orderCode": order_code,
        "amount": amount,
        "description": description,
        "returnUrl": return_url,
        "cancelUrl": cancel_url,
        "signature": signature
    }
    if buyer:
        body.update({
            "buyerName": buyer.get("name"),
            "buyerEmail": buyer.get("email"),
            "buyerPhone": buyer.get("phone")
        })

    resp = requests.post(url, json=body, headers=headers, timeout=15)
    print(">>> PayOS response:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()
