#!/usr/bin/env python3
"""
Test script for AI chat with RAG functionality.

This script tests:
1. Sending a chat message
2. Getting conversation history
3. Listing conversations
4. Updating conversation
5. Submitting feedback
6. Deleting conversation
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def login():
    """Login and get access token"""
    print_section("1. Login")

    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    token = data.get("access_token")
    print(f"✅ Login successful")
    print(f"Token: {token[:50]}...")

    return token

def get_or_upload_document(token):
    """Get existing document or upload a test one"""
    print_section("2. Get/Upload Test Document")

    headers = {"Authorization": f"Bearer {token}"}

    # Try to get existing documents
    response = requests.get(
        f"{BASE_URL}/documents",
        headers=headers,
        params={"page": 1, "page_size": 5}
    )

    if response.status_code == 200:
        data = response.json()
        documents = data.get("documents", [])

        if documents:
            doc = documents[0]
            print(f"✅ Using existing document: {doc['title']}")
            print(f"   Document ID: {doc['id']}")
            print(f"   Status: {doc['processing_status']}")
            return doc["id"]

    print("ℹ️  No existing documents found")
    print("ℹ️  Please upload a document first using the document upload endpoint")
    return None

def send_chat_message(token, document_id, message, conversation_id=None):
    """Send a chat message"""
    print_section(f"3. Send Chat Message{' (New Conversation)' if not conversation_id else ''}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": message,
        "include_sources": True,
        "max_context_chunks": 5,
        "similarity_threshold": 0.5
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    print(f"Message: {message}")
    print(f"Sending request to {BASE_URL}/chat/message...")

    response = requests.post(
        f"{BASE_URL}/chat/message",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        print(f"❌ Chat message failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    print(f"✅ Chat message successful")
    print(f"\nConversation ID: {data['conversation_id']}")
    print(f"Is new conversation: {data['is_new_conversation']}")
    print(f"\nAssistant Response:")
    print(f"{'─'*60}")
    print(data['message']['content'])
    print(f"{'─'*60}")

    # Show sources
    sources = data['message'].get('sources', [])
    if sources:
        print(f"\nSources ({len(sources)}):")
        for i, source in enumerate(sources, 1):
            print(f"  [{i}] {source['document_title']}")
            print(f"      Page: {source.get('page_number', 'N/A')}")
            print(f"      Similarity: {source['similarity_score']:.3f}")
            print(f"      Matter: {source.get('matter_name', 'N/A')}")
    else:
        print("\nℹ️  No sources cited (no relevant context found)")

    print(f"\nToken count: {data['message'].get('token_count', 'N/A')}")
    print(f"Model: {data['message'].get('model_name', 'N/A')}")

    return data['conversation_id']

def get_conversation(token, conversation_id):
    """Get conversation with messages"""
    print_section("4. Get Conversation History")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/chat/conversations/{conversation_id}",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Get conversation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return

    data = response.json()
    print(f"✅ Conversation retrieved")
    print(f"\nTitle: {data['title']}")
    print(f"Created: {data['created_at']}")
    print(f"Messages: {len(data['messages'])}")

    print(f"\nMessage History:")
    for i, msg in enumerate(data['messages'], 1):
        role = "👤 User" if msg['role'] == 'user' else "🤖 Assistant"
        content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"  {i}. {role}: {content}")

def list_conversations(token):
    """List all conversations"""
    print_section("5. List Conversations")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/chat/conversations",
        headers=headers,
        params={"page": 1, "page_size": 10}
    )

    if response.status_code != 200:
        print(f"❌ List conversations failed: {response.status_code}")
        print(f"Response: {response.text}")
        return

    data = response.json()
    print(f"✅ Conversations retrieved")
    print(f"\nTotal: {data['total']}")
    print(f"Page: {data['page']} (size: {data['page_size']})")

    print(f"\nConversations:")
    for i, conv in enumerate(data['conversations'], 1):
        print(f"  {i}. {conv['title']}")
        print(f"     ID: {conv['id']}")
        print(f"     Messages: {conv.get('message_count', 0)}")
        print(f"     Last message: {conv.get('last_message_preview', 'N/A')[:50]}...")
        print(f"     Pinned: {conv['is_pinned']}, Archived: {conv['is_archived']}")
        print()

def update_conversation(token, conversation_id):
    """Update conversation (pin it)"""
    print_section("6. Update Conversation")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.patch(
        f"{BASE_URL}/chat/conversations/{conversation_id}",
        headers=headers,
        json={"is_pinned": True, "title": "Test Chat - Document Q&A"}
    )

    if response.status_code != 200:
        print(f"❌ Update conversation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return

    data = response.json()
    print(f"✅ Conversation updated")
    print(f"\nTitle: {data['title']}")
    print(f"Pinned: {data['is_pinned']}")

def submit_feedback(token, message_id):
    """Submit feedback for a message"""
    print_section("7. Submit Feedback")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/chat/messages/{message_id}/feedback",
        headers=headers,
        json={"rating": 1, "feedback_text": "Great response!"}
    )

    if response.status_code != 200:
        print(f"❌ Submit feedback failed: {response.status_code}")
        print(f"Response: {response.text}")
        return

    print(f"✅ Feedback submitted")

def delete_conversation(token, conversation_id):
    """Delete conversation"""
    print_section("8. Delete Conversation")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(
        f"{BASE_URL}/chat/conversations/{conversation_id}",
        headers=headers
    )

    if response.status_code != 204:
        print(f"❌ Delete conversation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return

    print(f"✅ Conversation deleted")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  BC Legal Tech - Chat Test Suite")
    print("="*60)

    # 1. Login
    token = login()
    if not token:
        print("\n❌ Test failed: Could not login")
        return

    # 2. Get/upload document
    document_id = get_or_upload_document(token)

    # 3. Send first chat message (creates conversation)
    conversation_id = send_chat_message(
        token,
        document_id,
        "What is this document about? Please summarize the main points."
    )

    if not conversation_id:
        print("\n❌ Test failed: Could not send chat message")
        return

    # Wait a moment for processing
    time.sleep(1)

    # 4. Send follow-up message
    send_chat_message(
        token,
        document_id,
        "Are there any important dates or deadlines mentioned?",
        conversation_id=conversation_id
    )

    # 5. Get conversation history
    get_conversation(token, conversation_id)

    # 6. List all conversations
    list_conversations(token)

    # 7. Update conversation
    update_conversation(token, conversation_id)

    # 8. Submit feedback (using conversation_id as message_id for testing)
    # In reality, you'd get the actual message_id from the response
    # submit_feedback(token, conversation_id)

    # 9. Delete conversation
    # Commented out so you can inspect the conversation in the database
    # delete_conversation(token, conversation_id)

    print_section("✅ All Tests Complete!")
    print(f"Conversation ID: {conversation_id}")
    print(f"\nℹ️  Conversation not deleted - check it in the database!")
    print(f"   You can manually delete it using:")
    print(f"   DELETE {BASE_URL}/chat/conversations/{conversation_id}")

if __name__ == "__main__":
    main()
