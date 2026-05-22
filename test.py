import requests
url = "https://enterprise-procurement-backend-241537274385.us-central1.run.app/chat/stream"
headers = {"Authorization": "Bearer mock-secret-token"}
payload = {"message": "How much did we spend on TechCorp Inc.?"}

response = requests.post(url, headers=headers, json=payload, stream=True)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(response.text)
for chunk in response.iter_content(chunk_size=None):
    if chunk:
        print(chunk.decode())
