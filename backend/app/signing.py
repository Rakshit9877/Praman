import os
import json
import base64
import hashlib
from typing import Any
from pydantic import BaseModel
import nacl.signing
import nacl.encoding

# Load the repository-root .env so PRAMAN_SIGNING_SEED_B64 is available even when
# uvicorn is started without exporting it. Existing env vars always win.
try:
    from dotenv import load_dotenv

    load_dotenv(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        override=False,
    )
except Exception:  # pragma: no cover - dotenv is optional
    pass

def canonicalize(model_or_dict: Any) -> str:
    """
    Returns the exact UTF-8 JSON string that will be signed.
    This must match the browser's JSON.stringify format exactly.
    """
    if isinstance(model_or_dict, BaseModel):
        data = model_or_dict.model_dump(mode="json")
    elif isinstance(model_or_dict, dict):
        data = model_or_dict
    else:
        raise ValueError("Must be a Pydantic model or a dictionary")
        
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sign_payload(canonical_json: str) -> dict:
    """
    Signs the canonical JSON string and returns signature data.
    """
    seed_b64 = os.getenv("PRAMAN_SIGNING_SEED_B64", "")
    if not seed_b64:
        # Mock mode fallback key if not provided
        seed_bytes = b"mock_seed_" * 3 + b"12" 
    else:
        seed_bytes = base64.b64decode(seed_b64)
    
    signing_key = nacl.signing.SigningKey(seed_bytes)
    verify_key = signing_key.verify_key
    
    signed = signing_key.sign(canonical_json.encode("utf-8"))
    signature_b64 = base64.b64encode(signed.signature).decode("utf-8")
    
    pub_key_bytes = verify_key.encode()
    pub_key_b64 = base64.b64encode(pub_key_bytes).decode("utf-8")
    key_id = hashlib.sha256(pub_key_bytes).hexdigest()[:8]
    
    return {
        "signature_b64": signature_b64,
        "key_id": key_id,
        "public_key_b64": pub_key_b64
    }
