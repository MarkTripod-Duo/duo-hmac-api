# Overview

This project attempts to create a Docker image consisting of the Duo HMAC facility embedded in
an HTTP wrapper delivered via standard HTTP POST interactions. The envisioned use case is to 
allow software developers an easy to deploy micro service for calculating the HTTP Basic Authorization
HTTP header value that is required for each interaction with Cisco Duo public APIs.

## Requirements

* [Docker](https://www.docker.com/)
* [Python 3.x](https://www.python.org/)

### Optional (Development)
* [HTTPX](https://www.python-httpx.org/) Python library

## Installation

Clone the repository and build the Docker image.
```shell
# git clone https://github.com/MarkTripod-Duo/duo-hmac-api.git
# cd duo-hmac-api
# docker build -t duo-hmac-api .
```

## Usage

```shell
# docker run -d -p 8000:8000 -e IKEY=<Duo API IKEY> -e SKEY=<Duo API SKEY> -e HOST=<Duo API Hostname> --name duo-hmac duo-hmac-api
```

### Example

Once the Duo HMAC micro service container has been launched, a standard HTTP POST request can be sent on the
port defined in the `docker run` command (port 8000 in the example above). The HTTP POST **must** contain a
JSON body. The JSON body **must** contain the elements 'method', 'path', 'parameters'. The JSON **may** also
contain a 'header' element.

'method' - the HTTP method that will be used when making the request to the Duo API ('GET', 'POST', 'PUT', etc.)
'path' - the Duo API endpoint path ('/admin/v2/settings' for example)
'parameters' - the Duo API parameters that will be included in the request to the Duo API. (Should be a list of 
name/value pairs or a JSON object)

The response from the Duo HMAC microservice container will consist of a JSON object with 'uri', 'headers', and 
'body' elements.

For example:
```
{
    'body': '{
        "custom_supported_browsers":{},
        "disabled_groups":[],
        "enabled_groups":[],
        "enabled_status":"disabled"
        }',
    'headers': {
        'Authorization': 'Basic RElXOVhUMTRWSUlBSDNMNDI3STg6NDI4ZWJlMzUyOWUxMDQ3OWM3NmE2NDU3MGI3MjlkYTJiNjNiNDlkYTViNzQ1MTBhYTI1OWRmNTNiZDYxMjc3MGU1MGZkZDQxYWMyNjczYTUzNmIzZTA2NmJkM2MzNWEyNGIxNjdiZjZiYzEwNmNkOWZhMjA5NTc3YjI1Y2YxYzU=',
        'Content-type': 'application/json',
        'x-duo-date': 'Fri, 01 Aug 2025 13:20:12 -0000'
        },
    'uri': 'api-731c6826.duosecurity.com/admin/v2/passport/config'
}
```

The response values can then be used to directly interact with the Duo API.

## Testing

To perform a manual test of the Duo HMAC microservice container, a simple Python script has been provided in the `scripts/` folder.

```shell
# cd scripts
# python3 validate_container_verbose.py

Sending HTTP request to Duo HMAC micro service container [http://127.0.0.1:8000]...
HTTP Response code from Duo HMAC micro service: 200
Duo API URI: https://api-xxxxxxxx.duosecurity.com/admin/v2/passport/config
Duo API Body: {'custom_supported_browsers': {}, 'disabled_groups': [], 'enabled_groups': [], 'enabled_status': 'disabled'}
Duo API Headers: {'Authorization': 'Basic RElXOVhUMTRWSUlBSDNMNDI3STg6YzJhYjA1ZTQ0Yzg0NmEwMTk0NDM5MTlkNThkZTNjMTk2YTRiOGJiMWUzYTU0MTMzZmI3YTM1NWNmN2E4ZjNiMDgzNWJkNWE3MzMxMTQ3ZDM1YjgxODYwN2Y4ZmVjN2FjMzg2YjE3ZjhmMjI0ZDIyNTFhY2Y3OTU5N2JkZjM3MDE=', 'Content-type': 'application/json'}

#### Sending HTTP request to Duo Admin API...
HTTP Response code from Duo Admin API: 200
Duo Admin API Response: {'response': '', 'stat': 'OK'}
#
```

Additional testing can be performed by using the `validate_container_verbose.py` script as a model for customized testing needs.

## Issues

Issues can be reported via the [GitHub Issues](https://github.com/MarkTripod-Duo/duo-hmac-api/issues) page.