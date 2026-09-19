import nacl.signing
import nacl.encoding
import base64
import os
import hashlib

def generate_keys():
    # Generate random 32-byte seed for Ed25519
    seed = os.urandom(32)
    signing_key = nacl.signing.SigningKey(seed)
    verify_key = signing_key.verify_key
    
    seed_b64 = base64.b64encode(seed).decode('utf-8')
    pubkey_b64 = base64.b64encode(verify_key.encode()).decode('utf-8')
    
    key_id = hashlib.sha256(verify_key.encode()).hexdigest()[:8]
    
    print(f"Seed (PRAMAN_SIGNING_SEED_B64): {seed_b64}")
    print(f"Public Key (VITE_PRAMAN_PUBKEY): {pubkey_b64}")
    print(f"Key ID: {key_id}")

if __name__ == "__main__":
    generate_keys()
