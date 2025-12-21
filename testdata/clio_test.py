"""
Clio OAuth Test Script

A simple standalone FastAPI app to test Clio OAuth integration.

Setup:
1. Create a Clio app at https://app.clio.com/settings/developer_applications
2. Set redirect URI to: http://127.0.0.1:8000/api/integrations/clio/callback
3. Set environment variables:
   - CLIO_CLIENT_ID
   - CLIO_CLIENT_SECRET
4. Run: python clio_test.py
5. Visit: http://127.0.0.1:8001
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
import json

app = FastAPI(title="Clio OAuth Test")

# Clio region - change to "us", "ca", or "eu"
CLIO_REGION = os.getenv("CLIO_REGION", "ca")  # Default to Canada for BC
CLIO_BASE_URL = {
    "us": "https://app.clio.com",
    "ca": "https://ca.app.clio.com",
    "eu": "https://eu.app.clio.com"
}.get(CLIO_REGION, "https://app.clio.com")

# Load from environment variables (required)
CLIO_CLIENT_ID = os.getenv("CLIO_CLIENT_ID", "")
CLIO_CLIENT_SECRET = os.getenv("CLIO_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("CLIO_REDIRECT_URI", "http://127.0.0.1:8000/api/integrations/clio/callback")

if not CLIO_CLIENT_ID or not CLIO_CLIENT_SECRET:
    raise ValueError(
        "Missing required environment variables: CLIO_CLIENT_ID and CLIO_CLIENT_SECRET\n"
        "Set them before running this script."
    )

# Store token in memory for testing
stored_token = {}


@app.get("/")
def home():
    connected = "access_token" in stored_token
    if connected:
        return HTMLResponse(f"""
            <h1>BC Legal Tech - Clio Test</h1>
            <p style="color: green;">Connected to Clio</p>
            <ul>
                <li><a href="/matters">View Matters</a></li>
                <li><a href="/contacts">View Contacts</a></li>
                <li><a href="/documents">View Documents</a></li>
                <li><a href="/disconnect">Disconnect</a></li>
            </ul>
            <h3>Token Info:</h3>
            <pre>{json.dumps(stored_token, indent=2)}</pre>
        """)
    else:
        return HTMLResponse("""
            <h1>BC Legal Tech - Clio Test</h1>
            <p>Test OAuth integration with Clio</p>
            <a href="/connect" style="display: inline-block; padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px;">
                Connect to Clio
            </a>
        """)


@app.get("/connect")
def connect():
    # Request all common scopes for testing
    scopes = "matters:read contacts:read documents:read activities:read"
    auth_url = (
        f"{CLIO_BASE_URL}/oauth/authorize?"
        f"response_type=code&"
        f"client_id={CLIO_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={scopes}"
    )
    return RedirectResponse(url=auth_url)


@app.get("/api/integrations/clio/callback")
async def callback(code: str):
    global stored_token

    # Debug: Print what we're sending
    token_data = {
        "client_id": CLIO_CLIENT_ID,
        "client_secret": CLIO_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    print("=" * 50)
    print("TOKEN EXCHANGE REQUEST")
    print("=" * 50)
    print(f"URL: {CLIO_BASE_URL}/oauth/token")
    print(f"client_id: {token_data['client_id']}")
    print(f"client_secret: {token_data['client_secret'][:10]}...")
    print(f"grant_type: {token_data['grant_type']}")
    print(f"code: {token_data['code']}")
    print(f"redirect_uri: {token_data['redirect_uri']}")
    print("=" * 50)

    # Exchange code for token
    # Try with Basic Auth header (some OAuth servers prefer this)
    import base64
    credentials = base64.b64encode(f"{CLIO_CLIENT_ID}:{CLIO_CLIENT_SECRET}".encode()).decode()

    async with httpx.AsyncClient() as client:
        # First try: Basic Auth in header
        token_response = await client.post(
            f"{CLIO_BASE_URL}/oauth/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI
            }
        )

    print(f"Response status: {token_response.status_code}")
    print(f"Response body: {token_response.text}")
    print("=" * 50)

    if token_response.status_code != 200:
        return HTMLResponse(f"""
            <h1>Error</h1>
            <pre>{token_response.text}</pre>
            <a href="/">Back</a>
        """)

    stored_token = token_response.json()
    return RedirectResponse(url="/")


@app.get("/disconnect")
def disconnect():
    global stored_token
    stored_token = {}
    return RedirectResponse(url="/")


@app.get("/matters")
async def get_matters():
    if "access_token" not in stored_token:
        return RedirectResponse(url="/")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CLIO_BASE_URL}/api/v4/matters.json",
            headers={"Authorization": f"Bearer {stored_token['access_token']}"},
            params={"fields": "id,display_number,description,status,client{name}"}
        )

    data = response.json()

    return HTMLResponse(f"""
        <h1>Clio Matters</h1>
        <a href="/">Back</a>
        <pre>{json.dumps(data, indent=2)}</pre>
    """)


@app.get("/contacts")
async def get_contacts():
    if "access_token" not in stored_token:
        return RedirectResponse(url="/")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CLIO_BASE_URL}/api/v4/contacts.json",
            headers={"Authorization": f"Bearer {stored_token['access_token']}"},
            params={"fields": "id,name,type,primary_email_address,primary_phone_number"}
        )

    data = response.json()

    return HTMLResponse(f"""
        <h1>Clio Contacts</h1>
        <a href="/">Back</a>
        <pre>{json.dumps(data, indent=2)}</pre>
    """)


@app.get("/documents")
async def get_documents():
    if "access_token" not in stored_token:
        return RedirectResponse(url="/")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CLIO_BASE_URL}/api/v4/documents.json",
            headers={"Authorization": f"Bearer {stored_token['access_token']}"},
            params={"fields": "id,name,created_at,updated_at,content_type,matter{id,display_number}"}
        )

    data = response.json()

    return HTMLResponse(f"""
        <h1>Clio Documents</h1>
        <a href="/">Back</a>
        <pre>{json.dumps(data, indent=2)}</pre>
    """)



if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("Clio OAuth Test Server")
    print("=" * 50)
    print(f"Region: {CLIO_REGION.upper()} ({CLIO_BASE_URL})")
    print(f"Client ID: {CLIO_CLIENT_ID[:10]}..." if len(CLIO_CLIENT_ID) > 10 else f"Client ID: {CLIO_CLIENT_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()
    print("Visit: http://127.0.0.1:8000")
    print("=" * 50)

    uvicorn.run(app, host="127.0.0.1", port=8000)
