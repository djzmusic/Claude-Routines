import os
import logging
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = Flask(__name__)

# Clients are initialized once at startup so OAuth only runs on first launch
_gmail = None
_outlook = None


def _init_clients():
    global _gmail, _outlook
    errors = []

    gmail_creds = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials_gmail.json")
    if os.path.exists(gmail_creds):
        try:
            from gmail_client import GmailClient
            _gmail = GmailClient().authenticate()
            app.logger.info("Gmail connected")
        except Exception as e:
            errors.append(f"Gmail: {e}")
    else:
        app.logger.warning("Gmail credentials file not found — Gmail skipped")

    outlook_id = os.getenv("OUTLOOK_CLIENT_ID")
    if outlook_id:
        try:
            from outlook_client import OutlookClient
            _outlook = OutlookClient().authenticate()
            app.logger.info("Outlook connected")
        except Exception as e:
            errors.append(f"Outlook: {e}")
    else:
        app.logger.warning("OUTLOOK_CLIENT_ID not set — Outlook skipped")

    if errors:
        for e in errors:
            app.logger.error(e)

    return _gmail, _outlook


@app.route("/")
def index():
    gmail_ready = _gmail is not None
    outlook_ready = _outlook is not None
    return render_template("index.html", gmail_ready=gmail_ready, outlook_ready=outlook_ready)


@app.route("/api/cleanup", methods=["POST"])
def run_cleanup():
    from email_processor import EmailProcessor

    if not _gmail and not _outlook:
        return jsonify({
            "success": False,
            "error": "No email accounts connected. See README.md to set up Gmail and/or Outlook.",
        }), 400

    try:
        processor = EmailProcessor(gmail_client=_gmail, outlook_client=_outlook)
        results = processor.run()
        return jsonify({"success": True, "results": results})
    except Exception as e:
        app.logger.exception("Cleanup failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/status")
def status():
    return jsonify({
        "gmail": _gmail is not None,
        "outlook": _outlook is not None,
    })


if __name__ == "__main__":
    _init_clients()
    port = int(os.getenv("PORT", 5001))
    print(f"\n✓ Email Cleanup app running → http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
