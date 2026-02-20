"""POST request with JSON using the requests library."""
import requests

url = "https://httpbin.org/post"
data = {"name": "test"}

response = requests.post(url, json=data)

print("Status code:", response.status_code)
print("Response body:")
print(response.json())
