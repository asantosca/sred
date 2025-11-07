"""
Test script for end-to-end embedding generation pipeline.
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login to get token
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "testupload@example.com",
        "password": "TestUpload123!"
    }
)
login_response.raise_for_status()
login_data = login_response.json()
token = login_data["token"]["access_token"]

headers = {"Authorization": f"Bearer {token}"}
user_id = login_data["user"]["id"]

# Get the test matter ID
matters_response = requests.get(f"{BASE_URL}/matters", headers=headers)
matters_response.raise_for_status()
matters = matters_response.json()
print(f"DEBUG: Matters response type: {type(matters)}, value: {matters}")

# Check if it's a dict with 'items' or similar key
if isinstance(matters, dict):
    matters = matters.get('matters', matters.get('items', matters.get('data', [])))

if not matters or len(matters) == 0:
    print("No matters found. Creating a test matter...")
    matter_data = {
        "matter_number": "TEST-001",
        "client_name": "Test Client for Embedding",
        "case_type": "contract",
        "matter_status": "active",
        "description": "Test matter for embedding generation",
        "opened_date": "2025-01-01",
        "lead_attorney_user_id": user_id
    }
    create_matter_response = requests.post(
        f"{BASE_URL}/matters",
        headers=headers,
        json=matter_data
    )
    create_matter_response.raise_for_status()
    matter = create_matter_response.json()
    matter_id = matter["id"]
    print(f"   OK Created matter: {matter['client_name']} ({matter_id})")
else:
    matter_id = matters[0]["id"]
    print(f"Using matter: {matters[0]['client_name']} ({matter_id})")

# Upload document
print("\n1. Uploading test document...")
with open("test_embedding_doc.txt", "rb") as f:
    files = {"file": ("test_embedding_doc.txt", f, "text/plain")}
    data = {
        "matter_id": matter_id,
        "document_type": "contract",
        "document_title": "Employment Agreement - Embedding Test",
        "document_date": "2024-01-15"
    }
    upload_response = requests.post(
        f"{BASE_URL}/documents/upload/quick",
        headers=headers,
        files=files,
        data=data
    )

if upload_response.status_code != 200:
    print(f"Upload failed: {upload_response.status_code}")
    print(upload_response.text)
    exit(1)

document = upload_response.json()
document_id = document["id"]
print(f"   OK Document uploaded: {document_id}")
print(f"   Status: {document['processing_status']}")

# Monitor processing status
print("\n2. Monitoring document processing...")
max_wait = 60  # seconds
start_time = time.time()

while time.time() - start_time < max_wait:
    time.sleep(2)

    # Get document status
    doc_response = requests.get(
        f"{BASE_URL}/documents/{document_id}",
        headers=headers
    )
    doc_response.raise_for_status()
    doc = doc_response.json()

    status = doc["processing_status"]
    print(f"   Status: {status}", end="")

    if doc.get("text_extracted"):
        print(f" | Text extracted: {doc.get('word_count', 0)} words", end="")

    if doc.get("indexed_for_search"):
        print(f" | Indexed: YES", end="")

    print()  # newline

    if status == "embedded":
        print("\n   OK Document fully processed with embeddings!")
        break
    elif status in ["extraction_failed", "failed"]:
        print(f"\n   X Processing failed: {doc.get('extraction_error', 'Unknown error')}")
        exit(1)
else:
    print(f"\n   \! Timeout after {max_wait} seconds")
    exit(1)

# Check chunks and embeddings in database
print("\n3. Verifying embeddings in database...")
print("   (This would normally query the database directly)")
print(f"   Document ID: {document_id}")
print(f"   Processing status: {doc['processing_status']}")
print(f"   Indexed for search: {doc.get('indexed_for_search', False)}")

print("\nOK Embedding generation pipeline test complete!")
