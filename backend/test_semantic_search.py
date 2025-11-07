"""
Test semantic search functionality end-to-end.

This script:
1. Creates a test document with known content
2. Uploads it via the API
3. Processes it through the full pipeline (extraction → chunking → embedding)
4. Tests semantic search with various queries
5. Verifies results are accurate and relevant
"""
import asyncio
import requests
import json
from uuid import UUID

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials (from previous tests)
TEST_EMAIL = "search.test@example.com"
TEST_PASSWORD = "securepassword123"

def register_user():
    """Register a new test user if needed"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Search Test User",
            "company_name": "Test Law Firm"
        }
    )
    
    if response.status_code == 201:
        print("[OK] Registered new test user")
        return True
    elif response.status_code == 400 and "already registered" in response.json().get("detail", "").lower():
        print("[OK] User already exists")
        return True
    else:
        print(f"[FAIL] Registration failed: {response.status_code}")
        print(response.json())
        return False


def create_test_document():
    """Create a test document with known legal content"""
    content = """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into on January 15, 2024,
between Tech Innovations Inc. ("Employer") and Sarah Johnson ("Employee").

COMPENSATION
The Employee shall receive an annual base salary of $120,000 (one hundred twenty
thousand dollars), payable in bi-weekly installments. In addition, the Employee
may be eligible for an annual performance bonus of up to 20% of base salary,
at the sole discretion of the Employer.

BENEFITS
The Employee is entitled to:
- 15 days of paid vacation per year
- Comprehensive health insurance coverage
- 401(k) retirement plan with 5% employer matching
- Professional development budget of $5,000 annually

TERMINATION
Either party may terminate this Agreement with 30 days written notice. In the
event of termination without cause by the Employer, the Employee shall receive
severance pay equal to three months of base salary.

CONFIDENTIALITY
The Employee agrees to maintain strict confidentiality regarding all proprietary
information, trade secrets, and business strategies of the Employer, both during
and after employment.

NON-COMPETE
For a period of 12 months following termination of employment, the Employee
agrees not to work for any direct competitor of the Employer within a 50-mile
radius of the Employer's headquarters.

GOVERNING LAW
This Agreement shall be governed by the laws of the Province of British Columbia,
Canada.
"""

    with open("test_employment_contract.txt", "w") as f:
        f.write(content)

    print("[OK] Created test employment contract")
    return "test_employment_contract.txt"


def login():
    """Login and get JWT token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    if response.status_code != 200:
        print(f"[FAIL] Login failed: {response.status_code}")
        print(response.json())
        return None

    token = response.json()["access_token"]
    print("[OK] Logged in successfully")
    return token


def get_or_create_matter(token):
    """Get existing matter or create a new one"""
    headers = {"Authorization": f"Bearer {token}"}

    # Try to get existing matters
    response = requests.get(f"{BASE_URL}/matters", headers=headers)

    if response.status_code == 200:
        matters = response.json().get("matters", [])
        if matters:
            matter_id = matters[0]["id"]
            print(f"[OK] Using existing matter: {matter_id}")
            return matter_id

    # Create a new matter
    response = requests.post(
        f"{BASE_URL}/matters",
        headers=headers,
        json={
            "name": "Employment Law - Test Case",
            "description": "Test matter for semantic search",
            "status": "active"
        }
    )

    if response.status_code != 201:
        print(f"[FAIL] Failed to create matter: {response.status_code}")
        print(response.json())
        return None

    matter_id = response.json()["id"]
    print(f"[OK] Created new matter: {matter_id}")
    return matter_id


def upload_document(token, matter_id, file_path):
    """Upload document via quick upload"""
    headers = {"Authorization": f"Bearer {token}"}

    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "text/plain")}
        data = {
            "matter_id": matter_id,
            "document_type": "Contract",
            "title": "Employment Agreement - Sarah Johnson",
            "document_date": "2024-01-15",
            "confidentiality_level": "Standard"
        }

        response = requests.post(
            f"{BASE_URL}/documents/upload/quick",
            headers=headers,
            files=files,
            data=data
        )

    if response.status_code != 201:
        print(f"[FAIL] Upload failed: {response.status_code}")
        print(response.json())
        return None

    doc_id = response.json()["id"]
    print(f"[OK] Uploaded document: {doc_id}")
    return doc_id


async def process_document_pipeline(doc_id):
    """Process document through chunking and embedding pipeline"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.services.document_processor import DocumentProcessor

    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        processor = DocumentProcessor(session)

        # Process chunking
        print("  → Processing chunking...")
        chunking_success = await processor.process_chunking(UUID(doc_id))

        if not chunking_success:
            print("  [FAIL] Chunking failed!")
            return False

        print("  [OK] Chunking completed")

        # Process embeddings
        print("  → Generating embeddings...")
        embedding_success = await processor.process_embeddings(UUID(doc_id))

        if not embedding_success:
            print("  [FAIL] Embedding generation failed!")
            return False

        print("  [OK] Embeddings generated")

    await engine.dispose()
    return True


def test_semantic_search(token, matter_id):
    """Test semantic search with various queries"""
    headers = {"Authorization": f"Bearer {token}"}

    test_queries = [
        {
            "query": "What is the salary?",
            "expected_content": ["$120,000", "annual base salary"],
            "description": "Compensation query"
        },
        {
            "query": "What benefits does the employee receive?",
            "expected_content": ["vacation", "health insurance", "401(k)"],
            "description": "Benefits query"
        },
        {
            "query": "How much notice is required for termination?",
            "expected_content": ["30 days", "written notice"],
            "description": "Termination clause query"
        },
        {
            "query": "What are the non-compete restrictions?",
            "expected_content": ["12 months", "50-mile radius", "competitor"],
            "description": "Non-compete query"
        },
        {
            "query": "What is the severance pay?",
            "expected_content": ["three months", "base salary", "severance"],
            "description": "Severance query"
        }
    ]

    print("\n" + "="*60)
    print("TESTING SEMANTIC SEARCH")
    print("="*60)

    results_summary = []

    for i, test in enumerate(test_queries, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Query: '{test['query']}'")

        response = requests.post(
            f"{BASE_URL}/search/semantic",
            headers=headers,
            json={
                "query": test["query"],
                "matter_id": matter_id,
                "limit": 5,
                "similarity_threshold": 0.5
            }
        )

        if response.status_code != 200:
            print(f"  [FAIL] Search failed: {response.status_code}")
            print(f"  {response.json()}")
            results_summary.append({"test": test['description'], "passed": False})
            continue

        data = response.json()
        print(f"  [OK] Found {data['total_results']} results in {data['search_time_ms']:.2f}ms")

        if data['total_results'] == 0:
            print(f"  [FAIL] No results found!")
            results_summary.append({"test": test['description'], "passed": False})
            continue

        # Check if expected content is in results
        top_result = data['results'][0]
        content_lower = top_result['content'].lower()

        found_expected = []
        for expected in test['expected_content']:
            if expected.lower() in content_lower:
                found_expected.append(expected)

        if found_expected:
            print(f"  [OK] Found expected content: {', '.join(found_expected)}")
            print(f"  Similarity score: {top_result['similarity_score']:.3f}")
            print(f"  Chunk: {top_result['content'][:100]}...")
            results_summary.append({"test": test['description'], "passed": True, "score": top_result['similarity_score']})
        else:
            print(f"  [FAIL] Expected content not found in results")
            print(f"  Got: {content_lower[:100]}...")
            results_summary.append({"test": test['description'], "passed": False})

    # Print summary
    print("\n" + "="*60)
    print("SEARCH TEST SUMMARY")
    print("="*60)

    passed = sum(1 for r in results_summary if r.get('passed', False))
    total = len(results_summary)

    for result in results_summary:
        status = "[OK] PASSED" if result.get('passed', False) else "[FAIL] FAILED"
        score_info = f" (score: {result['score']:.3f})" if 'score' in result else ""
        print(f"{status} - {result['test']}{score_info}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    return passed == total


def main():
    """Run the complete semantic search test"""
    print("\n" + "="*60)
    print("SEMANTIC SEARCH END-TO-END TEST")
    print("="*60 + "\n")

    # Step 1: Create test document
    print("Step 1: Creating test document")
    file_path = create_test_document()

    # Step 2: Login
    print("\nStep 2: Authenticating")
    token = login()
    if not token:
        return

    # Step 3: Get or create matter
    print("\nStep 3: Setting up matter")
    matter_id = get_or_create_matter(token)
    if not matter_id:
        return

    # Step 4: Upload document
    print("\nStep 4: Uploading document")
    doc_id = upload_document(token, matter_id, file_path)
    if not doc_id:
        return

    # Step 5: Process document through pipeline
    print("\nStep 5: Processing document pipeline")
    success = asyncio.run(process_document_pipeline(doc_id))
    if not success:
        return

    # Step 6: Test semantic search
    print("\nStep 6: Testing semantic search")
    all_passed = test_semantic_search(token, matter_id)

    # Final result
    print("\n" + "="*60)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED! Semantic search is working correctly!")
    else:
        print("[WARNING] SOME TESTS FAILED. Review results above.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
