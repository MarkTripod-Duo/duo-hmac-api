"""
Script to validate HTTP access to Duo HMAC calculator container
"""
import sys
import json

import httpx


def main():
    """
    Main function to send a POST request with predefined data to the local Duo HMAC
    Docker container and handle the response to perform a subsequent Duo Admin API request.

    Raises:
        SystemExit: If the Duo Admin API response status code is not 200 or if the
            'stat' field in the response JSON is not 'ok'.
    """
    # Instantiate a basic httpx client instance with SSL verification disabled
    client = httpx.Client(verify=False)

    # Basic HTTP POST body data to be used for validation of the Duo HMAC micro service
    # Docker container. Also used in validating the calculated Authorization header value
    # against the Duo Admin API.
    post_data = {
            "method": "POST",
            "path": "/admin/v2/passport/config",
            "parameters": {
                    "custom_supported_browsers": {},
                    "disabled_groups": [],
                    "enabled_groups": [],
                    "enabled_status": "disabled"
                    },
            "headers": {},
            }

    # Generate the Duo API Authorization data
    print(f"Sending HTTP request to Duo HMAC micro service container [http://127.0.0.1:8000]...")
    resp: httpx.Response = client.post("http://127.0.0.1:8000", json=post_data)

    print(f"HTTP Response code from Duo HMAC micro service: {resp.status_code}")

    # Collect the response from the Duo HMAC micro service Docker container
    if resp.status_code == 200:
        resp_dict = json.loads(resp.json())
        uri = f"https://{resp_dict['uri']}"
        body_json = json.loads(resp_dict['body'])

        print(f"Duo API URI: {uri}")
        print(f"Duo API Body: {body_json}")
        print(f"Duo API Headers: {resp_dict['headers']}")

        # Validate the generated Authorization data against the Duo Admin API
        duo_api_resp = client.post(url=uri, json=body_json, headers=resp_dict['headers'])
        if duo_api_resp.status_code != 200:
            sys.exit(-1)
        else:
            duo_api_resp_dict = duo_api_resp.json()
            if duo_api_resp_dict['stat'] == 'OK':
                sys.exit(0)
    else:
        print(f"Unexpected HTTP response from Duo HMAC micro service: {resp.text}")
        sys.exit(-1)


if __name__ == "__main__":
    main()
