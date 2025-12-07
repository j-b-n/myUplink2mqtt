#!/usr/bin/env python3
"""CLI helper to obtain a myUplink OAuth2 access token via authorization code flow.

This script prints an authorization URL, prompts for the returned code, exchanges it for a
Bearer token, and writes the token to the standard myUplink token path used by the project.
"""

import logging
import os
import sys
import time

from requests_oauthlib import OAuth2Session

from myuplink2mqtt.utils.myuplink_utils import (
    MYUPLINK_API_BASE,
    TOKEN_FILENAME,
    load_config,
    token_saver,
)

# OAuth endpoints and defaults
AUTHORIZE_URL = f"{MYUPLINK_API_BASE}/oauth/authorize"
TOKEN_URL = f"{MYUPLINK_API_BASE}/oauth/token"
DEFAULT_REDIRECT_URL = "https://www.marshflattsfarm.org.uk/nibeuplink/oauth2callback/index.php"
DEFAULT_SCOPE = "READSYSTEM offline_access"
DEFAULT_STATE = "x"


def main():
    """Run the authorization-code flow and persist the resulting token."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    client_id, client_secret = load_config()
    if not client_id or not client_secret:
        logging.error(
            "Client credentials not found. Set MYUPLINK_CLIENT_ID/SECRET or ~/.myUplink_API_Config.json."
        )
        sys.exit(1)

    redirect_url = os.getenv("MYUPLINK_REDIRECT_URI", DEFAULT_REDIRECT_URL)
    scope = os.getenv("MYUPLINK_SCOPE", DEFAULT_SCOPE)
    state = os.getenv("MYUPLINK_STATE", DEFAULT_STATE)

    session = OAuth2Session(
        client_id=client_id,
        scope=scope,
        redirect_uri=redirect_url,
        state=state,
    )

    auth_url, _ = session.authorization_url(AUTHORIZE_URL)
    logging.info("Browse to the authorization URL, approve access, and copy the returned code.")
    logging.info("Authorization URL: %s", auth_url)

    authorization_code = input("Enter the authorization code: ").strip()
    if len(authorization_code) < 20:
        logging.error("Authorization code is too short to be valid.")
        sys.exit(1)

    try:
        token = session.fetch_token(
            token_url=TOKEN_URL,
            code=authorization_code,
            include_client_id=True,
            client_secret=client_secret,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Token exchange failed: %s", exc)
        sys.exit(1)
    finally:
        session.close()

    if token.get("token_type", "").lower() != "bearer":
        logging.error("Invalid token_type in response: %s", token.get("token_type"))
        sys.exit(1)

    # Ensure expires_at exists for downstream tooling
    if "expires_at" not in token and "expires_in" in token:
        token["expires_at"] = time.time() + float(token["expires_in"])

    try:
        token_saver(token)
    except OSError as exc:
        logging.error("Failed to save token to %s: %s", TOKEN_FILENAME, exc)
        sys.exit(1)

    logging.info("Token saved to %s", TOKEN_FILENAME)


if __name__ == "__main__":
    main()
