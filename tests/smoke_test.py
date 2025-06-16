# -*- coding: utf-8 -*-
"""
Smoke test for the Transcritor PDF API service.

This test assumes that the `transcritor-pdf` service, as orchestrated by
the `modular-dashboard-adv`'s `docker-compose.yml`, is running and
accessible at the specified URL (typically http://localhost:8002).

It checks the /health/ endpoint for a successful response.
"""
import sys
import os

# Try to import requests, fall back to urllib if not found
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    import urllib.request
    import json
    from http.client import HTTPResponse # For type hinting

# Configuration for the service
# Based on the port mapping in modular-dashboard-adv/docker-compose.yml for transcritor_pdf
SERVICE_BASE_URL = os.getenv("TRANSCRITOR_PDF_BASE_URL", "http://localhost:8002")
HEALTH_ENDPOINT = f"{SERVICE_BASE_URL}/health/"

def run_smoke_test():
    """
    Runs the smoke test against the /health/ endpoint.
    """
    print(f"--- Running Smoke Test for Transcritor PDF API ---")
    print(f"Targeting health endpoint: {HEALTH_ENDPOINT}")

    try:
        if REQUESTS_AVAILABLE:
            print("Using 'requests' library...")
            response = requests.get(HEALTH_ENDPOINT, timeout=10) # 10 second timeout
            status_code = response.status_code
            try:
                response_json = response.json()
            except requests.exceptions.JSONDecodeError:
                response_json = None
                print(f"Warning: Response was not valid JSON. Raw text: {response.text[:200]}")
        else:
            print("Using 'urllib.request' library...")
            try:
                with urllib.request.urlopen(HEALTH_ENDPOINT, timeout=10) as http_response: # type: HTTPResponse
                    status_code = http_response.status
                    response_body_bytes = http_response.read()
                    try:
                        response_json = json.loads(response_body_bytes.decode('utf-8'))
                    except json.JSONDecodeError:
                        response_json = None
                        print(f"Warning: Response was not valid JSON. Raw text: {response_body_bytes.decode('utf-8', 'ignore')[:200]}")
            except urllib.error.URLError as e:
                print(f"Error connecting to service with urllib: {e}")
                if hasattr(e, 'code'): # For HTTPError
                    status_code = e.code
                else:
                    status_code = None # Network error, no HTTP status
                response_json = None


        print(f"Response Status Code: {status_code}")

        if status_code == 200:
            print("Health endpoint returned HTTP 200 OK.")
            if response_json:
                print(f"Response JSON: {response_json}")
                # The health endpoint in src/main.py returns {"status": "ok"}
                if response_json.get("status") == "ok":
                    print("SUCCESS: Health check passed! Service reports 'ok'.")
                    return True
                else:
                    print(f"FAILURE: Health check response JSON did not contain 'status: ok'. Found: {response_json.get('status')}")
                    return False
            else:
                # If it's 200 OK but no JSON, it's still a partial success for a basic smoke test.
                # However, our health endpoint is expected to return JSON.
                print("FAILURE: Health check response was 200 OK, but response was not valid JSON or JSON was empty.")
                return False
        else:
            print(f"FAILURE: Health check failed. Expected status code 200, got {status_code}.")
            if response_json:
                 print(f"Error Response JSON: {response_json}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"FAILURE: Could not connect to the service at {SERVICE_BASE_URL}.")
        print(f"Error details (requests): {e}")
        return False
    except Exception as e:
        # Catch any other exceptions (like timeout with urllib, etc.)
        print(f"FAILURE: An unexpected error occurred during the smoke test: {e}")
        return False

if __name__ == "__main__":
    print("Prerequisites for this smoke test:")
    print(f"1. The 'transcritor-pdf' service (and its dependencies like the database) must be running.")
    print(f"   This is typically started via `docker compose up` from the 'modular-dashboard-adv' project directory.")
    print(f"2. The service must be accessible at: {SERVICE_BASE_URL}")
    print(f"   (The health endpoint is {HEALTH_ENDPOINT})")
    print(f"3. If using the 'requests' library, it must be installed (`pip install requests`).")
    print("-" * 40)

    if run_smoke_test():
        print("-" * 40)
        print("Smoke test PASSED.")
        sys.exit(0)
    else:
        print("-" * 40)
        print("Smoke test FAILED.")
        sys.exit(1)
