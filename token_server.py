"""
token_server.py
Web-based Kite token refresh page
Access at: http://34.60.172.174/token
"""
from flask import Flask, request, redirect, render_template_string
from kiteconnect import KiteConnect
from dotenv import load_dotenv, set_key
import subprocess, os
from pathlib import Path

load_dotenv()

app = Flask(__name__)

API_KEY    = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
ENV_FILE   = Path("/home/ubuntu/trading-agent/.env")

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kite Token Refresh</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Arial, sans-serif;
      background: #0f1117;
      color: #ffffff;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }
    .card {
      background: #1a1d27;
      border-radius: 16px;
      padding: 32px 24px;
      max-width: 420px;
      width: 100%;
      box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }
    .logo { font-size: 2rem; margin-bottom: 8px; }
    h1 { font-size: 1.4rem; margin-bottom: 4px; color: #00cc66; }
    .subtitle { color: #888; font-size: 0.9rem; margin-bottom: 28px; }
    .status-box {
      background: #12151f;
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 24px;
      font-size: 0.9rem;
    }
    .status-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .status-row:last-child { margin-bottom: 0; }
    .label { color: #888; }
    .value { font-weight: bold; }
    .green { color: #00cc66; }
    .red { color: #ff4444; }
    .yellow { color: #ffaa00; }
    .btn {
      display: block;
      width: 100%;
      padding: 14px;
      border: none;
      border-radius: 10px;
      font-size: 1rem;
      font-weight: bold;
      cursor: pointer;
      text-decoration: none;
      text-align: center;
      margin-bottom: 12px;
    }
    .btn-primary { background: #00cc66; color: #000; }
    .btn-secondary { background: #2a2d3a; color: #fff; }
    .btn-danger { background: #ff4444; color: #fff; }
    .input-group { margin-bottom: 16px; }
    .input-group label { display: block; color: #888; font-size: 0.85rem; margin-bottom: 6px; }
    .input-group input {
      width: 100%;
      padding: 12px;
      background: #12151f;
      border: 1px solid #333;
      border-radius: 8px;
      color: #fff;
      font-size: 0.95rem;
    }
    .alert {
      padding: 12px 16px;
      border-radius: 8px;
      margin-bottom: 20px;
      font-size: 0.9rem;
    }
    .alert-success { background: #0d2e1a; border: 1px solid #00cc66; color: #00cc66; }
    .alert-error   { background: #2e0d0d; border: 1px solid #ff4444; color: #ff4444; }
    .steps { margin-bottom: 24px; }
    .step {
      display: flex;
      align-items: flex-start;
      margin-bottom: 12px;
      font-size: 0.9rem;
    }
    .step-num {
      background: #00cc66;
      color: #000;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 0.75rem;
      flex-shrink: 0;
      margin-right: 10px;
      margin-top: 1px;
    }
    .divider { border: none; border-top: 1px solid #2a2d3a; margin: 20px 0; }
  </style>
</head>
<body>
<div class="card">
  <div class="logo">📈</div>
  <h1>MiniMax Trading Agent</h1>
  <p class="subtitle">Kite Token Refresh — Daily Setup</p>

  {% if message %}
  <div class="alert {{ 'alert-success' if success else 'alert-error' }}">
    {{ message }}
  </div>
  {% endif %}

  <div class="status-box">
    <div class="status-row">
      <span class="label">Agent Status</span>
      <span class="value {{ 'green' if agent_running else 'red' }}">
        {{ '● Running' if agent_running else '● Stopped' }}
      </span>
    </div>
    <div class="status-row">
      <span class="label">Token Status</span>
      <span class="value {{ 'green' if token_valid else 'red' }}">
        {{ '✓ Valid' if token_valid else '✗ Expired / Missing' }}
      </span>
    </div>
    <div class="status-row">
      <span class="label">Mode</span>
      <span class="value yellow">{{ mode }}</span>
    </div>
  </div>

  <div class="steps">
    <div class="step">
      <div class="step-num">1</div>
      <div>Click the button below to open Zerodha login</div>
    </div>
    <div class="step">
      <div class="step-num">2</div>
      <div>Login with your Zerodha ID + password + TOTP</div>
    </div>
    <div class="step">
      <div class="step-num">3</div>
      <div>After login, copy the <strong>request_token</strong> from the redirect URL</div>
    </div>
    <div class="step">
      <div class="step-num">4</div>
      <div>Paste it below and click Submit</div>
    </div>
  </div>

  <a href="{{ login_url }}" target="_blank" class="btn btn-primary">
    🔐 Open Zerodha Login
  </a>

  <hr class="divider">

  <form method="POST" action="/token/submit">
    <div class="input-group">
      <label>Paste request_token here</label>
      <input type="text" name="request_token"
             placeholder="e.g. dCshwQZxvfQUd58VcyX..."
             autocomplete="off" autocorrect="off" spellcheck="false" />
    </div>
    <button type="submit" class="btn btn-primary">
      ✅ Submit Token &amp; Restart Agent
    </button>
  </form>

  <hr class="divider">

  <form method="POST" action="/token/restart">
    <button type="submit" class="btn btn-secondary">
      🔄 Restart Agent Only
    </button>
  </form>

</div>
</body>
</html>
"""


def get_agent_status() -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "trading-agent"],
            capture_output=True, text=True
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False


def get_token_status() -> bool:
    token = os.getenv("KITE_ACCESS_TOKEN", "")
    return bool(token and len(token) > 10)


def get_mode() -> str:
    return os.getenv("TRADING_MODE", "paper").upper()


@app.route("/")
@app.route("/token")
def index():
    kite      = KiteConnect(api_key=API_KEY)
    login_url = kite.login_url()
    return render_template_string(HTML,
        login_url     = login_url,
        agent_running = get_agent_status(),
        token_valid   = get_token_status(),
        mode          = get_mode(),
        message       = None,
        success       = False
    )


@app.route("/token/submit", methods=["POST"])
def submit_token():
    request_token = request.form.get("request_token", "").strip()
    kite          = KiteConnect(api_key=API_KEY)
    login_url     = kite.login_url()

    if not request_token:
        return render_template_string(HTML,
            login_url=login_url,
            agent_running=get_agent_status(),
            token_valid=get_token_status(),
            mode=get_mode(),
            message="❌ Please paste a request_token first.",
            success=False
        )

    try:
        # Generate access token
        data         = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]

        # Save to .env file
        set_key(str(ENV_FILE), "KITE_ACCESS_TOKEN", access_token)

        # Reload env and restart agent
        subprocess.run(["sudo", "systemctl", "restart", "trading-agent"], check=True)

        return render_template_string(HTML,
            login_url=login_url,
            agent_running=True,
            token_valid=True,
            mode=get_mode(),
            message="✅ Token saved and agent restarted successfully! Ready to trade.",
            success=True
        )

    except Exception as e:
        return render_template_string(HTML,
            login_url=login_url,
            agent_running=get_agent_status(),
            token_valid=False,
            mode=get_mode(),
            message=f"❌ Error: {str(e)} — Make sure the token is fresh (not already used).",
            success=False
        )


@app.route("/token/restart", methods=["POST"])
def restart_agent():
    kite      = KiteConnect(api_key=API_KEY)
    login_url = kite.login_url()
    try:
        subprocess.run(["sudo", "systemctl", "restart", "trading-agent"], check=True)
        message = "✅ Agent restarted successfully."
        success = True
    except Exception as e:
        message = f"❌ Restart failed: {str(e)}"
        success = False

    return render_template_string(HTML,
        login_url=login_url,
        agent_running=get_agent_status(),
        token_valid=get_token_status(),
        mode=get_mode(),
        message=message,
        success=success
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
