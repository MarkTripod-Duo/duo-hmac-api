import unittest
from fastapi.testclient import TestClient
import logging
import json

from main import app


class TestDuoHmacAPI(unittest.TestCase):
    def setUp(self):
        # Set up test environment variables
        logging.disable(logging.CRITICAL)
        self.client = TestClient(app)

    def tearDown(self):
        # Re-enable logging after each test
        logging.disable(logging.NOTSET)

    def test_get_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Unsupported method. Try POST"})

    def test_post_missing_method(self):
        response = self.client.post("/", json={
            "path": "/auth/v2/check"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "missing 'method' element in the request body"})

    def test_post_missing_path(self):
        response = self.client.post("/", json={
            "method": "GET"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "missing 'path' element in the request body"})

    def test_post_invalid_parameter_type(self):
        response = self.client.post("/", json={
            "method": "GET",
            "path": "/auth/v2/check",
            "parameters": {
                "count": 123  # non-string value
            }
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "parameter 'count' must be a string"})

    def test_post_successful_no_params(self):
        return_value = {
            "uri": r'api-\w{8}\.duosecurity\.com.*',
            "body": None,
            "headers": {
                "x-duo-date": "Thu, 30 Jul 2025 00:00:00 -0000",
                "Authorization": "Basic SOMEBASE64STRING="
            }
        }

        response = self.client.post("/", json={
            "method": "GET",
            "path": "/auth/v2/check",
            "parameters": {},
            "headers": {}
        })

        resp_dict: dict = json.loads(response.json())

        self.assertEqual(response.status_code, 200)
        self.assertRegex(resp_dict['uri'], return_value['uri'])
        self.assertEqual(resp_dict['body'], return_value['body'])
        self.assertIn('Authorization', resp_dict['headers'])

    def test_post_successful_with_params_and_headers(self):
        return_value = {
            "uri": r'api-\w{8}\.duosecurity\.com.*',
            "body": None,
            "headers": {
                "x-duo-date": "Thu, 30 Jul 2025 00:00:00 -0000",
                "Authorization": "Basic SOMEBASE64STRING=",
                "Custom-Header": "test-value"
            }
        }

        response = self.client.post("/", json={
            "method": "GET",
            "path": "/auth/v2/check",
            "parameters": {
                "user_id": "12345"
            },
            "headers": {
                "Custom-Header": "test-value"
            }
        })

        resp_dict: dict = json.loads(response.json())

        self.assertEqual(response.status_code, 200)
        self.assertRegex(resp_dict['uri'], return_value['uri'])
        self.assertEqual(resp_dict['body'], return_value['body'])
        self.assertIn('Authorization', resp_dict['headers'])
        self.assertIn('x-duo-date', resp_dict['headers'])


    def test_post_successful_with_body(self):
        return_value = {
            "uri": r'api-\w{8}\.duosecurity\.com.*',
            "body": '{"policy_name":"new-test-policy"}',
            "headers": {
                "x-duo-date": "Thu, 30 Jul 2025 00:00:00 -0000",
                "Authorization": "Basic SOMEBASE64STRING=",
                "Content-type": "application/json"
            }
        }

        response = self.client.post("/", json={
            "method": "POST",
            "path": "/admin/v2/policies",
            "parameters": {"policy_name": "new-test-policy"},
            "headers": {},
        })

        resp_dict: dict = json.loads(response.json())

        self.assertEqual(response.status_code, 200)
        self.assertRegex(resp_dict['uri'], return_value['uri'])
        self.assertEqual(resp_dict['body'], return_value['body'])
        self.assertIn('Authorization', resp_dict['headers'])
        self.assertIn('x-duo-date', resp_dict['headers'])


if __name__ == '__main__':
    unittest.main()
