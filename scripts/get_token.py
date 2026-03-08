"""
scripts/get_token.py
Run this every morning to get a fresh Zerodha access token.
Usage: python scripts/get_token.py

It will:
1. Print the Zerodha login URL
2. Ask you to paste the request_token from the redirect URL
3. Generate an access token and save it to your .env file
"""
import os
import sys
import webbrowser
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kiteconnect import KiteConnect
from dotenv import load_dotenv, set_key

load_dotenv()

API_KEY    = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
ENV_FILE   = Path(__file__).parent.parent / ".env"

if not API_KEY or not API_SECRET:
    print("ERROR: KITE_API_KEY and KITE_API_SECRET not found in .env file")
    sys.exit(1)

kite     = KiteConnect(api_key=API_KEY)
login_url = kite.login_url()

print("=" * 60)
print("ZERODHA DAILY TOKEN REFRESH")
print("=" * 60)
print(f"\nStep 1: Opening Zerodha login in your browser...")
print(f"URL: {login_url}\n")

try:
    webbrowser.open(login_url)
except Exception:
    pass

print("Step 2: Login with your Zerodha credentials + TOTP")
print("Step 3: After login, Zerodha redirects to a URL like:")
print("        http://127.0.0.1:5000/callback?request_token=XXXXX&...")
print("\nStep 4: Copy ONLY the request_token value from that URL")
print("        (the part after 'request_token=' and before '&')\n")

request_token = input("Paste your request_token here: ").strip()

if not request_token:
    print("ERROR: No token entered. Exiting.")
    sys.exit(1)

try:
    data         = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = data["access_token"]
    print(f"\nAccess token generated successfully!")
    print(f"Token: {access_token[:20]}...")

    # Save to .env file
    set_key(str(ENV_FILE), "KITE_ACCESS_TOKEN", access_token)
    print(f"Token saved to .env file.")
    print("\nYou can now start the agent: python main.py")

except Exception as e:
    print(f"\nERROR generating session: {e}")
    print("Make sure your API Key and Secret are correct in .env")
    sys.exit(1)
