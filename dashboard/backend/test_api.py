import os
import sys
from fastapi.testclient import TestClient

# Ensure context paths are aligned
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
import database

def run_tests():
    print("========================================")
    print("  DASHBOARD ENDPOINT TESTS")
    print("========================================")
    
    with TestClient(app) as client:
        # 1. Create a test user
        print("-> Creating 'testuser' account...")
        database.create_user("testuser", "testpassword123")
        
        # 2. Login and get token
        print("-> Logging in to get JWT token...")
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "testpassword123"
        })
        
        if response.status_code != 200:
            print(f"[FAIL] Login failed! Status: {response.status_code}")
            return
            
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[PASS] Successfully logged in. Token acquired: {token[:15]}...")
        
        # 3. Test all endpoints
        endpoints = [
            "/api/overview",
            "/api/signals",
            "/api/macro",
            "/api/cot",
            "/api/debate"
        ]
        
        for ep in endpoints:
            print(f"\nEvaluating: GET {ep}")
            res = client.get(ep, headers=headers)
            print(f"Status Code: {res.status_code}")
            
            if res.status_code == 200:
                data = res.json()
                print(f"Data Summary: returned {len(data)} root records. Keys: {list(data.keys())[:5]}")
                print(f"Sample Payload: {str(data)[:150]}...")
            else:
                print(f"[FAIL] Endpoint error -> {res.text}")

        # Cleanup test user softly
        database.deactivate_user("testuser")
        
    print("\n========================================")
    print("  TESTING COMPLETE")
    print("========================================")

if __name__ == "__main__":
    run_tests()
