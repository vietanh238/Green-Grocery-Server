import hmac
import hashlib

def verify_checksum(payload: dict, checksum_key: str, checksum_field: str = "signature") -> bool:
    if checksum_field not in payload:
        return False

    received_signature = payload[checksum_field]
    data_to_sign = {k: v for k, v in payload.items() if k != checksum_field}

    parts = []
    for key in sorted(data_to_sign.keys()):
        value = data_to_sign[key]

        if value is None:
            value_str = ""
        elif isinstance(value, bool):
            value_str = str(value).lower()
        else:
            value_str = str(value)

        parts.append(f"{key}={value_str}")

    canonical_string = "&".join(parts)

    generated_digest = hmac.new(
        checksum_key.encode("utf-8"),
        canonical_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


    return hmac.compare_digest(generated_digest, received_signature)

def generate_signature(order_code, amount, description, return_url, cancel_url, checksum_key):
    raw_data = f"amount={amount}&cancelUrl={cancel_url}&description={description}&orderCode={order_code}&returnUrl={return_url}"
    signature = hmac.new(
        checksum_key.encode("utf-8"),
        raw_data.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature