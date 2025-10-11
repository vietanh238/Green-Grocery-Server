import hmac
import hashlib

def verify_checksum(payload: dict, checksum_key: str, checksum_field: str = "checksum") -> bool:
    if checksum_field not in payload:
        return False

    received = payload[checksum_field]
    data = {k: v for k, v in payload.items() if k != checksum_field}

    parts = []
    for k in sorted(data.keys()):
        parts.append(f"{k}={data[k]}")
    canonical = "&".join(parts)

    digest = hmac.new(
        checksum_key.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(digest, received)

def generate_signature(order_code, amount, description, return_url, cancel_url, checksum_key):
    raw_data = f"amount={amount}&cancelUrl={cancel_url}&description={description}&orderCode={order_code}&returnUrl={return_url}"
    signature = hmac.new(
        checksum_key.encode("utf-8"),
        raw_data.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature