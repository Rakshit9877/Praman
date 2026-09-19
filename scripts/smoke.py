import requests
import sys
import time

BASE_URL = "http://localhost:8000"

def run_smoke_test():
    print("Starting smoke test...")
    
    # 1. Reset
    print("Resetting DB...")
    res = requests.post(f"{BASE_URL}/api/demo/reset")
    res.raise_for_status()

    # 2. Seed demo
    print("Seeding demo data...")
    res = requests.post(f"{BASE_URL}/api/demo/seed")
    res.raise_for_status()
    worker_id = res.json()["worker_id"]
    print(f"Worker seeded: {worker_id}")

    # 3. Create session (just to test endpoint)
    print("Testing session creation...")
    res = requests.post(f"{BASE_URL}/api/workers/session")
    res.raise_for_status()
    print("Session created.")

    # 4. Issue Passport
    print("Issuing passport...")
    res = requests.post(f"{BASE_URL}/api/passports", json={"worker_id": worker_id})
    res.raise_for_status()
    passport = res.json()
    
    passport_id = json.loads(passport["payload_canonical"])["passport_id"]
    print(f"Passport issued: {passport_id}")
    
    # 5. Fetch Passport
    print("Fetching passport...")
    res = requests.get(f"{BASE_URL}/api/passports/{passport_id}")
    res.raise_for_status()
    print("Smoke test passed successfully!")

if __name__ == "__main__":
    import json
    run_smoke_test()
