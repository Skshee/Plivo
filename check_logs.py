import os
from plivo import RestClient
from dotenv import load_dotenv

load_dotenv()

PLIVO_AUTH_ID = os.environ.get('PLIVO_AUTH_ID')
PLIVO_AUTH_TOKEN = os.environ.get('PLIVO_AUTH_TOKEN')

if not PLIVO_AUTH_ID or not PLIVO_AUTH_TOKEN:
    print("Credentials not found in .env")
    exit(1)

client = RestClient(auth_id=PLIVO_AUTH_ID, auth_token=PLIVO_AUTH_TOKEN)

try:
    response = client.calls.list(limit=20)
    print(f"Found {len(response)} recent calls overall. Filtering for your number...")
    found = False
    for call in response:
        if "7995724447" in call.to_number or "799574447" in call.to_number:
            found = True
            print("-" * 30)
            print(f"To: {call.to_number}")
            print(f"From: {call.from_number}")
            print(f"State: {call.call_state}")
            print(f"Direction: {call.call_direction}")
            print(f"Start Time: {getattr(call, 'initiation_time', 'N/A')}")
            print(f"Hangup Cause: {getattr(call, 'hangup_cause_name', 'N/A')}")
            print(f"Hangup Code: {getattr(call, 'hangup_cause_code', 'N/A')}")
    if not found:
        print("Your number was not found in the last 20 calls. Plivo might be rejecting it before it even hits the call logs, or someone else made 20 calls since you tried.")
except Exception as e:
    print(f"Error fetching logs: {e}")
