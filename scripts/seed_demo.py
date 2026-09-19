import requests
import sys

def seed_demo():
    print("Seeding demo data...")
    res = requests.post("http://localhost:8000/api/demo/seed")
    if res.status_code == 200:
        print("Success:", res.json())
    else:
        print(f"Failed ({res.status_code}):", res.text)
        sys.exit(1)

if __name__ == "__main__":
    seed_demo()
