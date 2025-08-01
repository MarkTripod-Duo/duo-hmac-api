"""
API wrapper for Duo HMAC calculator
"""
from __future__ import annotations

import os
import logging

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from pydantic import BaseModel
from logging.handlers import RotatingFileHandler

from json import dumps
from duo_hmac.duo_hmac import DuoHmac


REQUIRED_ENV_VARS = {}

class Params(BaseModel):
    """
    Represents the parameters required for an HTTP request.

    This class models the details required to make an HTTP request, including
    the HTTP method, target URL path, optional parameters, and request headers.
    It ensures data validation and provides a structured way to manage request
    parameters.

    Attributes:
        method (str): The HTTP method to use (e.g., GET, POST).
        path (str): The URL path for the request.
        parameters (Optional[dict[str, str]]): Optional query parameters or
            request data.
        headers (Optional[dict[str, str]]): Optional headers for the HTTP
            request.
    """
    method: str
    path: str
    parameters: Optional[dict[str, str]] = None
    headers: Optional[dict[str, str]] = None


class LoggingFormatter(logging.Formatter):
    """
    Custom logging formatter for log messages.

    This class defines a custom formatter for logging messages that provides a clear and detailed
    log format. It utilizes structured message formatting with time, log level, logger name,
    module, function, line number, and message content to improve log readability and debugging
    efficiency.
    """

    def format(self, record):
        log_message_format = \
            '{asctime} | {levelname:<9} | {name:15} | {module:<14} : {funcName:>30}() [{lineno:_>5}] | {message}'
        formatter = logging.Formatter(log_message_format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


def get_logger(
        name: str = __name__,
        *,
        log_level: str = "INFO",
        log_to_console: bool = True,
        log_to_file: bool = True,
        max_log_bytes: int = 25000000,
        backup_log_count: int = 3,
        log_path: Optional[str] = None,
        ) -> logging.Logger:
    """Get default_logger instance

    Args:
        name: Name of the default_logger instance to create or retrieve
        log_level: The message severity level to assign to the new default_logger instance
        log_to_console: Flag to enable console logging
        log_to_file: Flag to enable file logging
        max_log_bytes: The maximum size in bytes of log file
        backup_log_count: The number of backup log files to retain
        log_path: The path to the directory where log files will be stored.
                    If not provided, the default is '/var/log/duo/'.

    Returns:
        logging.Logger instance

    """
    queued_msgs = []
    tmp_logger = logging.getLogger(name)
    tmp_logger.setLevel(logging.getLevelName(log_level))

    log_path = log_path or os.getenv('LOG_PATH') or os.path.join(os.getcwd(), 'logs')

    # Console handler
    if log_to_console:
        queued_msgs.append(f"Configuring console logging handler ...")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(LoggingFormatter())
        tmp_logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        queued_msgs.append(f"Configuring file logging handler ...")
        logfile_name = "duo_hmac.log"
        Path(log_path).mkdir(parents=True, exist_ok=True)
        log_file = os.path.join(log_path, logfile_name)
        file_handler = RotatingFileHandler(
                filename=log_file,
                encoding="utf-8",
                maxBytes=max_log_bytes,
                backupCount=backup_log_count
                )
        file_handler.setFormatter(LoggingFormatter())
        tmp_logger.addHandler(file_handler)

    tmp_logger.info("")
    tmp_logger.info(" --- [ Logging started for %s (%s)] ---", name, log_level)
    tmp_logger.info(" Log file path: %s", log_path)
    tmp_logger.info(" Log file size: %s, max count: %s", max_log_bytes, backup_log_count)
    tmp_logger.debug(f"New default_logger name: {name!r} - Instance: {tmp_logger} (ID: {hex(id(tmp_logger))})")

    for handler in tmp_logger.handlers:
        tmp_logger.debug(f"Handler: {handler!r}")

    if len(queued_msgs) > 0:
        for msg in queued_msgs:
            tmp_logger.debug(f"Queued message: {msg}")

    return tmp_logger


def mask_secret(secret: str) -> str:
    """
    Obscures sensitive information contained in a string by masking the middle characters
    to enhance security and prevent disclosure of sensitive data.

    Args:
        secret (str): The input string containing the sensitive information to be masked.
            If the string is empty or None, a default value of '****' is returned.

    Returns:
        str: The masked string with the middle characters replaced by asterisks while
        retaining the first 4 and last 4 characters. For empty input, returns a default
        masked string of '****'.
    """
    return secret[:4] + 4 * '*' + secret[-4:] if secret else 4 * '*'


def get_env_vars():
    """
    Retrieves and sets required environment variables for Duo Security API integration.

    This function defines a global dictionary `REQUIRED_ENV_VARS` containing essential
    environment variables required for integration with the Duo Security API. These
    variables are retrieved from the environment, with default values assigned if the
    corresponding environment variables are not set. For security reasons, sensitive
    values are masked before being logged.

    Logs the masked values of the environment variables using the `logger.info` method.
    It highlights essential information for debugging and tracing without exposing
    sensitive data.

    Raises:
        None

    Returns:
        None
    """
    global REQUIRED_ENV_VARS
    REQUIRED_ENV_VARS = {
            'IKEY': os.getenv("IKEY", 'DIABCDEFGHIJKLMNOPQR'),
            'SKEY': os.getenv("SKEY", '1234567890abcdefghijklmnopqrstuvwxyz1234'),
            'HOST': os.getenv("HOST", 'https://api-XXXXXXXX.duosecurity.com')
            }
    logger.info(f"IKEY {mask_secret(REQUIRED_ENV_VARS['IKEY'])}")
    logger.info(f"SKEY {mask_secret(REQUIRED_ENV_VARS['SKEY'])}")
    logger.info(f"HOST {mask_secret(REQUIRED_ENV_VARS['HOST'])}")


def validate_environment_variables():
    """
    Validates the presence of required environment variables and logs missing variables.

    This function checks if all required environment variables, as defined in the
    REQUIRED_ENV_VARS dictionary, are set. If any of these variables are missing, it
    logs the missing variable names as an error and terminates the application.

    Raises:
        SystemExit: Exits the program with a status code of 1 if any required
        environment variables are missing.
    """
    missing_vars = [var_name for var_name, value in REQUIRED_ENV_VARS.items() if value is None]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)


def validate_data(data: dict):
    """
    Validates the structure and values within a dictionary representing data typically used
    in a request. Ensures required keys are present and checks that all parameter values
    are strings if the 'parameters' key exists.

    Args:
        data (dict): A dictionary containing keys such as 'method', 'path', and optionally
            'parameters'. Validations are performed to ensure their presence and the correct type.

    Returns:
        dict or None: Returns a dictionary containing an error message if the data does
            not meet validation criteria. Returns None if the data is valid.
    """
    if 'method' not in data:
        return {"message": "missing 'method' element in the request body"}
    if 'path' not in data:
        return {"message": "missing 'path' element in the request body"}
    if 'parameters' not in data:
        return {"message": "missing 'parameter' element in the request body"}
    return None


def get_client_ip(request) -> str:
    """
    Get the client's real IP address using common proxy headers.

    Args:
        request: FastAPI request object

    Returns:
        str: The client's IP address

    The function checks headers in the following order:
    1. X-Forwarded-For
    2. X-Real-IP
    3. X-Client-IP
    4. CF-Connecting-IP (Cloudflare)
    5. True-Client-IP
    6. client.host from direct connection
    """
    client_ips = []
    if forwarded_for := request.headers.get("X-Forwarded-For"):
        client_ips.append(f"X-Forwarded-For: {forwarded_for}")

    if real_ip := request.headers.get("X-Real-IP"):
        client_ips.append(f"X-Real-IP: {real_ip}")

    if client_ip := request.headers.get("X-Client-IP"):
        client_ips.append(f"X-Client-IP: {client_ip}")

    if cf_ip := request.headers.get("CF-Connecting-IP"):
        client_ips.append(f"CF-Connecting-IP: {cf_ip}")

    if true_client_ip := request.headers.get("True-Client-IP"):
        client_ips.append(f"True-Client-IP: {true_client_ip}")

    client_ips.append(f"client.host: {request.client.host}")

    return ';'.join(client_ips)


### Main wrapper logic
logger = get_logger("duo_hmac", log_level="INFO")
get_env_vars()
validate_environment_variables()

duo = DuoHmac(REQUIRED_ENV_VARS['IKEY'],
              REQUIRED_ENV_VARS['SKEY'],
              REQUIRED_ENV_VARS['HOST'], )

app = FastAPI(debug=False,
              title="Duo HMAC calculator",
              description="API wrapper for Duo HMAC calculator",
              version="1.0",
              )

@app.get("/")
async def root(request: Request,):
    client_ip = get_client_ip(request)
    logger.debug(f"Unsupported method. Try POST. [{client_ip}]")
    return {"message": "Unsupported method. Try POST"}


@app.post("/")
async def root(data: dict, request: Request,):
    validation_error = validate_data(data)
    if validation_error:
        logger.error(f"Validation error: {validation_error} [{get_client_ip(request)}]")
        return validation_error
    duo_data = {
            'http_method': data['method'].upper(),
            'api_path': data['path'],
            'parameters': data.get('parameters'),
            'in_headers': data.get('headers')
            }

    url, body, headers = duo.get_authentication_components(**duo_data)
    return dumps({
            'uri': url,
            'body': body,
            'headers': headers
            }, ensure_ascii=False, separators=(',', ':'))
