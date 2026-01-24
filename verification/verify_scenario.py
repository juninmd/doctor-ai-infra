import requests
import sys
import time

def verify_scenario():
    url = "http://localhost:8000/chat"
    payload = {
        "message": "Why is the frontend crashing?",
        "history": []
    }

    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to backend: {e}")
        return False

    data = response.json()
    print("Response received.")

    # We expect the final answer or the steps to contain clues about the troubleshooting process.
    # The 'response' field contains the final answer.
    # The 'steps' field contains the intermediate steps.

    final_response = data.get("response", "")
    steps = data.get("steps", [])

    print(f"\nFinal Response: {final_response}\n")

    # Check for key phrases in the entire interaction (steps + final response)
    full_text = final_response + str(steps)

    checks = {
        "CrashLoopBackOff": False,
        "ConnectionRefused": False,
        "MAINTENANCE": False
    }

    for check in checks:
        if check in full_text:
            checks[check] = True
            print(f"[PASS] Found '{check}'")
        else:
            print(f"[FAIL] Did not find '{check}'")

    if all(checks.values()):
        print("\nSUCCESS: All troubleshooting steps verified.")
        return True
    else:
        print("\nFAILURE: Missing expected troubleshooting details.")
        return False

if __name__ == "__main__":
    # Wait a bit for server to start if run immediately after
    time.sleep(2)
    if verify_scenario():
        sys.exit(0)
    else:
        sys.exit(1)
