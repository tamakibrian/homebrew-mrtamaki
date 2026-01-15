"""
HTTP client for 1lookup API
Handles all API requests with proper error handling and timeouts.
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print(
        "ERROR: 'requests' package not found. Install with: pip install requests",
        file=sys.stderr,
    )
    sys.exit(2)


class OneLookupClient:
    """Client for interacting with the 1lookup API."""

    # API Configuration
    BASE_URL = "https://app.1lookup.io/api"
    DEFAULT_TIMEOUT = 10

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the 1lookup API client.

        Args:
            api_key: API key (if None, will look in env/config)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or self._get_api_key()
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "API key not found. Set ONELOOKUP_API_KEY environment variable "
                "or create ~/.shell-v1.1/one_lookup.toml"
            )

    def _get_api_key(self) -> Optional[str]:
        """
        Get API key from environment variable or config file.

        Returns:
            API key string or None
        """
        # Try environment variable first
        api_key = os.environ.get("ONELOOKUP_API_KEY")
        if api_key:
            return api_key

        # Try config file
        config_paths = [
            Path.home() / ".shell-v1.1" / "one_lookup.toml",
            Path.home() / ".shell-v1.1" / "one_lookup.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    content = config_path.read_text()

                    if config_path.suffix == ".toml":
                        # Simple TOML parsing for api_key line
                        for line in content.split("\n"):
                            if line.strip().startswith("api_key"):
                                # Extract value after = and remove quotes
                                value = line.split("=", 1)[1].strip()
                                return value.strip('"').strip("'")

                    elif config_path.suffix == ".json":
                        data = json.loads(content)
                        return data.get("api_key")

                except Exception as e:
                    print(
                        f"Warning: Failed to read {config_path}: {e}", file=sys.stderr
                    )

        return None

    def _make_request(
        self, endpoint: str, payload: Dict[str, Any], method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            endpoint: API endpoint path
            payload: Request payload
            method: HTTP method

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: On network errors
            ValueError: On invalid JSON response
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            # Store response for error handling
            response_text = response.text

            # Check for non-200 status
            if response.status_code != 200:
                error_data = {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response_text or f"HTTP {response.status_code}",
                    "url": url,
                }
                return error_data

            # Parse JSON
            try:
                return response.json()
            except json.JSONDecodeError as e:
                return {
                    "error": True,
                    "message": f"Invalid JSON response: {str(e)}",
                    "raw_response": response_text[:500],  # First 500 chars
                }

        except requests.exceptions.Timeout:
            return {
                "error": True,
                "message": f"Request timed out after {self.timeout} seconds",
                "url": url,
            }

        except requests.exceptions.ConnectionError as e:
            return {"error": True, "message": f"Connection error: {str(e)}", "url": url}

        except requests.exceptions.RequestException as e:
            return {"error": True, "message": f"Request failed: {str(e)}", "url": url}

    def ip_lookup(self, ip: str) -> Dict[str, Any]:
        """
        Look up information about an IP address.

        Args:
            ip: IP address to look up

        Returns:
            API response dictionary
        """
        return self._make_request("v1/ip", {"ip": ip})

    def email_verify(self, email: str) -> Dict[str, Any]:
        """
        Verify an email address.

        Args:
            email: Email address to verify

        Returns:
            API response dictionary
        """
        return self._make_request("v1/email", {"email": email})

    def email_append(
        self,
        first_name: str,
        last_name: str,
        city: str,
        zip_code: str,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find email address from personal information.

        Args:
            first_name: First name
            last_name: Last name
            city: City
            zip_code: ZIP code
            address: Street address (optional)

        Returns:
            API response dictionary
        """
        input_data = {
            "firstName": first_name,
            "lastName": last_name,
            "city": city,
            "zip": zip_code,
        }

        if address:
            input_data["address"] = address

        payload = {"type": "email-append", "input": input_data}

        return self._make_request("lookup", payload)

    def reverse_email_append(self, email: str) -> Dict[str, Any]:
        """
        Find person details from email address.

        Args:
            email: Email address to look up

        Returns:
            API response dictionary
        """
        payload = {"type": "reverse-email-append", "input": email}

        return self._make_request("lookup", payload)

    def reverse_ip_append(self, ip: str) -> Dict[str, Any]:
        """
        Find details from IP address.

        Args:
            ip: IP address to look up

        Returns:
            API response dictionary
        """
        payload = {"type": "reverse-ip-append", "input": ip}

        return self._make_request("lookup", payload)
