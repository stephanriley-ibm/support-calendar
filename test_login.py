#!/usr/bin/env python
"""Test script to verify login endpoint works"""
import requests
import json

url = "http://localhost:8000/api/auth/users/login/"
data = {
    "username": "sriley",
    "password": "3l3m3nt@L"
}

print(f"Testing login endpoint: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print("-" * 50)

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Made with Bob
