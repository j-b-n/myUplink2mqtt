#!/usr/bin/env python3
"""Domoticz Authentication Diagnostic Tool.

This script helps diagnose authentication issues with Domoticz.

Usage:
    python demo_domoticz_auth_diagnostic.py --domoticz-host 10.0.0.100
    python demo_domoticz_auth_diagnostic.py --domoticz-host 10.0.0.100 --domoticz-username admin --domoticz-password mypassword
"""

import argparse
import logging
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


def print_header(title):
    """Print a formatted header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print a formatted section."""
    print()
    print("-" * 70)
    print(f"  {title}")
    print("-" * 70)


def test_no_auth(host, port):
    """Test Domoticz without authentication."""
    print_section("TEST 1: No Authentication")
    print()

    url = f"http://{host}:{port}/json.htm?type=command&param=getStatus"

    try:
        response = requests.get(url, timeout=5)
        print(f"  URL: {url}")
        print(f"  Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            print("  ✓ SUCCESS: Authentication is NOT required (open access)")
            try:
                data = response.json()
                print(f"  Server Time: {data.get('ServerTime', 'N/A')}")
                return True
            except Exception:
                pass
            return True
        elif response.status_code == 401:
            print("  i Information: Authentication IS required")
            return False
        else:
            print(f"  ? Unexpected status code: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  ✗ CONNECTION ERROR: Cannot reach {host}:{port}")
        print("  Please verify the host and port are correct")
        return False
    except requests.exceptions.Timeout:
        print(f"  ✗ TIMEOUT: No response from {host}:{port}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_with_auth(host, port, username, password):
    """Test Domoticz with authentication."""
    print_section(f"TEST 2: With '{username}' / '{password}' Credentials")
    print()

    url = f"http://{host}:{port}/json.htm?type=command&param=getStatus"

    try:
        auth = HTTPBasicAuth(username, password)
        response = requests.get(url, auth=auth, timeout=5)

        print(f"  URL: {url}")
        print(f"  Username: {username}")
        print(f"  Password: {'*' * len(password)}")
        print(f"  Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            print("  ✓ SUCCESS: Credentials are accepted!")
            try:
                data = response.json()
                print(f"  Server Time: {data.get('ServerTime', 'N/A')}")
                return True
            except Exception:
                pass
            return True
        elif response.status_code == 401:
            print("  ✗ FAILED: Credentials were rejected (401 Unauthorized)")
            return False
        else:
            print(f"  ? Unexpected status code: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  ✗ CONNECTION ERROR: Cannot reach {host}:{port}")
        return False
    except requests.exceptions.Timeout:
        print(f"  ✗ TIMEOUT: No response from {host}:{port}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_root_path(host, port):
    """Test Domoticz root path."""
    print_section("TEST 3: Root Path Access")
    print()

    url = f"http://{host}:{port}/"

    try:
        response = requests.get(url, timeout=5)

        print(f"  URL: {url}")
        print(f"  Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            print("  ✓ Domoticz is running and accessible")

            # Check for Domoticz markers
            if "domoticz" in response.text.lower():
                print("  ✓ Domoticz HTML detected")

            # Get version from ETag
            etag = response.headers.get("ETag", "N/A")
            print(f"  Version/ETag: {etag}")
            return True
        else:
            print(f"  ? Unexpected status code: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  ✗ CONNECTION ERROR: Cannot reach {host}:{port}")
        print("  Domoticz may not be running or host/port is incorrect")
        return False
    except requests.exceptions.Timeout:
        print(f"  ✗ TIMEOUT: No response from {host}:{port}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def print_recommendations(no_auth_works, with_auth_works, credentials_tested):
    """Print recommendations based on test results."""
    print_header("ANALYSIS & RECOMMENDATIONS")
    print()

    if no_auth_works:
        print("  🟢 FINDING: Domoticz is accessible WITHOUT authentication")
        print()
        print("  ✓ How to use the script:")
        print("    python demo_domoticz_json.py --domoticz-host 10.0.0.100")
        print()
        print("  i Note: You do NOT need to provide username/password")
        print()

    elif with_auth_works:
        print("  🟢 FINDING: Domoticz accepted your credentials")
        print()
        username, password = credentials_tested
        print("  ✓ How to use the script:")
        print("    python demo_domoticz_json.py \\")
        print("      --domoticz-host 10.0.0.100 \\")
        print(f"      --domoticz-username {username} \\")
        print(f"      --domoticz-password {password}")
        print()

    else:
        print("  🔴 FINDING: Could not authenticate to Domoticz")
        print()
        print("  Possible causes:")
        print("  1. Username/password are incorrect")
        print("  2. Domoticz uses a different authentication method")
        print("  3. Domoticz requires an API token instead of basic auth")
        print()
        print("  ✓ Steps to troubleshoot:")
        print("    1. Open http://10.0.0.100:8080/ in your browser")
        print("    2. If prompted for login, try those credentials")
        print("    3. Check Domoticz Settings → System → Security")
        print("    4. Verify username and password there")
        print("    5. Look for API token or authorization settings")
        print()
        print("  i If authentication is not enabled:")
        print("    python demo_domoticz_json.py --domoticz-host 10.0.0.100")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Domoticz Authentication Diagnostic Tool")

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

    parser.add_argument(
        "--domoticz-username",
        default="admin",
        metavar="USERNAME",
        help="Username to test (default: admin)",
    )

    parser.add_argument(
        "--domoticz-password",
        default="domoticz",
        metavar="PASSWORD",
        help="Password to test (default: domoticz)",
    )

    args = parser.parse_args()

    setup_logging()

    print_header("DOMOTICZ AUTHENTICATION DIAGNOSTIC TOOL")

    print()
    print(f"  Target: http://{args.domoticz_host}:{args.domoticz_port}")
    print()

    # Test 1: No auth
    no_auth_works = test_no_auth(args.domoticz_host, args.domoticz_port)

    # Test 2: With auth (only if no auth didn't work)
    if no_auth_works:
        with_auth_works = False
        credentials_tested = None
    else:
        with_auth_works = test_with_auth(
            args.domoticz_host,
            args.domoticz_port,
            args.domoticz_username,
            args.domoticz_password,
        )
        credentials_tested = (args.domoticz_username, args.domoticz_password)

    # Test 3: Root path
    test_root_path(args.domoticz_host, args.domoticz_port)

    # Recommendations
    print_recommendations(no_auth_works, with_auth_works, credentials_tested)

    # Final summary
    print_header("NEXT STEPS")
    print()
    print("  1. Run the appropriate command based on recommendations above")
    print("  2. If still having issues:")
    print("     - Check Domoticz Settings → System → Security")
    print("     - Review Domoticz documentation for API authentication")
    print("     - Check Domoticz logs for error messages")
    print()


if __name__ == "__main__":
    main()
