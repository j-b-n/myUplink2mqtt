#!/usr/bin/env python3
"""Test multiple Domoticz credentials interactively.

This script lets you test different username/password combinations
to find what works with your Domoticz instance.

Usage:
    python demo_domoticz_test_credentials.py --domoticz-host 10.0.0.100
"""

import argparse

import requests
from requests.auth import HTTPBasicAuth


def test_credentials(host, port, username, password):
    """Test a single username/password combination.

    Returns:
        tuple: (success: bool, status_code: int, message: str)
    """
    url = f"http://{host}:{port}/json.htm?type=command&param=getStatus"

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            timeout=5,
        )

        if response.status_code == 200:
            return True, response.status_code, "✓ SUCCESS"
        else:
            return False, response.status_code, f"✗ Failed (status {response.status_code})"

    except requests.exceptions.Timeout:
        return False, None, "✗ Timeout"
    except requests.exceptions.ConnectionError:
        return False, None, "✗ Connection error"
    except Exception as e:
        return False, None, f"✗ Error: {e}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Domoticz Credentials")

    parser.add_argument(
        "--domoticz-host",
        required=True,
        metavar="HOST",
        help="Domoticz host/IP address",
    )

    parser.add_argument(
        "--domoticz-port",
        type=int,
        default=8080,
        metavar="PORT",
        help="Domoticz port (default: 8080)",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print("  DOMOTICZ CREDENTIALS TESTER")
    print("=" * 70)
    print()
    print(f"  Target: http://{args.domoticz_host}:{args.domoticz_port}")
    print()

    # Common credential combinations to try
    credential_sets = [
        ("admin", "domoticz"),
        ("admin", "admin"),
        ("admin", ""),
        ("", ""),
        ("", "password"),
        ("domoticz", "domoticz"),
        ("pi", "raspberry"),
        ("root", "root"),
    ]

    print("  Trying common credentials...")
    print()
    print("  " + "-" * 66)
    print("  | Username      | Password       | Result")
    print("  " + "-" * 66)

    success_found = False

    for username, password in credential_sets:
        success, _status, message = test_credentials(
            args.domoticz_host,
            args.domoticz_port,
            username,
            password,
        )

        user_display = f"'{username}'" if username else "(empty)"
        pass_display = f"'{password}'" if password else "(empty)"

        # Truncate if too long
        user_display = (user_display[:14]).ljust(14)
        pass_display = (pass_display[:14]).ljust(14)

        print(f"  | {user_display} | {pass_display} | {message}")

        if success:
            success_found = True

    print("  " + "-" * 66)
    print()

    if success_found:
        print("  ✓ Found working credentials above!")
        print()
        print("  Use with the script:")
        print("    python demo_domoticz_json.py \\")
        print(f"      --domoticz-host {args.domoticz_host} \\")
        print("      --domoticz-username USERNAME \\")
        print("      --domoticz-password PASSWORD")
        print()
    else:
        print("  i None of the common credentials worked.")
        print()
        print("  You may need to:")
        print("  1. Check Domoticz Web UI (http://10.0.0.100:8080/) for actual credentials")
        print("  2. Go to Settings → System → Security")
        print("  3. Look for Username and Password settings")
        print("  4. Or manually test with:")
        print()
        print("    python demo_domoticz_test_credentials.py \\")
        print(f"      --domoticz-host {args.domoticz_host} \\")
        print()
        print("    Then supply your own credentials:")
        print()
        print("    curl -u USERNAME:PASSWORD \\")
        print(f"      http://{args.domoticz_host}:8080/json.htm?type=command&param=getStatus")
        print()


if __name__ == "__main__":
    main()
