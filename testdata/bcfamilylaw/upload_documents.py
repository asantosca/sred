"""
Upload benchmark documents to BC Legal Tech via API.

This script:
1. Authenticates with the API
2. Creates matters from benchmark (or uses existing ones)
3. Uploads each document to its corresponding matter
4. Tracks upload status and processing

Usage:
    python upload_documents.py [--base-url URL] [--email EMAIL] [--password PASSWORD]

Environment variables (alternative to command line args):
    TEST_BASE_URL - API base URL (default: http://localhost:8000)
    TEST_EMAIL - User email for authentication
    TEST_PASSWORD - User password for authentication
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import date
from typing import Optional

import requests


class APIClient:
    """Simple API client for BC Legal Tech."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.access_token: Optional[str] = None
        self.session = requests.Session()

    def login(self, email: str, password: str) -> bool:
        """Authenticate and get access token."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                # Token is nested under 'token' object
                token_data = data.get("token", {})
                self.access_token = token_data.get("access_token")
                if self.access_token:
                    self.session.headers["Authorization"] = f"Bearer {self.access_token}"
                    return True
                else:
                    print("No access token in response")
                    return False
            else:
                print(f"Login failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def get_matters(self) -> list:
        """Get list of matters."""
        response = self.session.get(f"{self.base_url}/api/v1/matters")
        if response.status_code == 200:
            data = response.json()
            # Response is paginated with 'matters' array
            return data.get('matters', [])
        return []

    def create_matter(self, matter_data: dict) -> Optional[dict]:
        """Create a new matter."""
        response = self.session.post(
            f"{self.base_url}/api/v1/matters",
            json=matter_data
        )
        if response.status_code == 201:
            return response.json()
        print(f"Failed to create matter: {response.status_code}")
        print(response.text)
        return None

    def upload_document(
        self,
        file_path: Path,
        matter_id: str,
        document_type: str,
        document_title: str,
        document_date: str,
        confidentiality_level: str = "standard_confidential"
    ) -> Optional[dict]:
        """Upload a document via the quick upload endpoint."""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
                data = {
                    'matter_id': matter_id,
                    'document_type': document_type,
                    'document_title': document_title,
                    'document_date': document_date,
                    'confidentiality_level': confidentiality_level
                }

                response = self.session.post(
                    f"{self.base_url}/api/v1/documents/upload/quick",
                    files=files,
                    data=data
                )

                if response.status_code == 201:
                    return response.json()
                else:
                    print(f"Upload failed: {response.status_code}")
                    print(response.text)
                    return None
        except Exception as e:
            print(f"Upload error: {e}")
            return None

    def get_document_status(self, document_id: str) -> Optional[dict]:
        """Get document processing status."""
        response = self.session.get(f"{self.base_url}/api/v1/documents/{document_id}")
        if response.status_code == 200:
            return response.json()
        return None

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type based on file extension."""
        ext = file_path.suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
        }
        return mime_types.get(ext, 'application/octet-stream')


def wait_for_processing(client: APIClient, document_id: str, timeout: int = 120) -> bool:
    """Wait for document processing to complete."""
    print(f"    Waiting for processing...", end='', flush=True)
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = client.get_document_status(document_id)
        if status:
            processing_status = status.get('processing_status', 'unknown')
            if processing_status in ['embedded', 'completed']:
                print(f" Done! (status: {processing_status})")
                return True
            elif processing_status == 'failed':
                print(f" FAILED")
                return False

        print('.', end='', flush=True)
        time.sleep(3)

    print(f" TIMEOUT")
    return False


def main():
    parser = argparse.ArgumentParser(description='Upload benchmark documents to BC Legal Tech')
    parser.add_argument('--base-url', default=os.environ.get('TEST_BASE_URL', 'http://localhost:8000'),
                        help='API base URL')
    parser.add_argument('--email', default=os.environ.get('TEST_EMAIL'),
                        help='User email for authentication')
    parser.add_argument('--password', default=os.environ.get('TEST_PASSWORD'),
                        help='User password for authentication')
    parser.add_argument('--skip-processing-wait', action='store_true',
                        help='Skip waiting for document processing')
    args = parser.parse_args()

    # Validate credentials
    if not args.email or not args.password:
        print("Error: Email and password are required.")
        print("Provide via --email/--password or TEST_EMAIL/TEST_PASSWORD environment variables.")
        sys.exit(1)

    # Load benchmark
    script_dir = Path(__file__).parent
    benchmark_file = script_dir / "bc_family_law_benchmark_with_files.json"

    if not benchmark_file.exists():
        print(f"Error: Benchmark file not found: {benchmark_file}")
        print("Run extract_documents.py first to create document files.")
        sys.exit(1)

    with open(benchmark_file, 'r', encoding='utf-8') as f:
        benchmark = json.load(f)

    documents = benchmark['documents']
    benchmark_matters = benchmark.get('matters', [])
    print(f"Loaded {len(documents)} documents across {len(benchmark_matters)} matters from benchmark")
    print()

    # Initialize API client
    print(f"Connecting to: {args.base_url}")
    client = APIClient(args.base_url)

    # Authenticate
    print(f"Authenticating as: {args.email}")
    if not client.login(args.email, args.password):
        print("Authentication failed!")
        sys.exit(1)
    print("Authentication successful!")
    print()

    # Create or find matters
    print("=" * 60)
    print("SETTING UP MATTERS")
    print("=" * 60)
    print()

    existing_matters = client.get_matters()
    existing_by_name = {m.get('client_name'): m for m in existing_matters}

    # Map benchmark matter_id to actual API matter_id
    matter_id_map = {}

    for bm_matter in benchmark_matters:
        matter_name = bm_matter['client_name']
        bm_matter_id = bm_matter['matter_id']

        if matter_name in existing_by_name:
            api_matter = existing_by_name[matter_name]
            matter_id_map[bm_matter_id] = str(api_matter['id'])
            print(f"[EXISTS] {matter_name} -> {api_matter['id']}")
        else:
            new_matter = client.create_matter({
                "matter_number": bm_matter['matter_number'],
                "client_name": matter_name,
                "matter_type": bm_matter['matter_type'],
                "description": bm_matter['description'],
                "opened_date": str(date.today())
            })
            if new_matter:
                matter_id_map[bm_matter_id] = str(new_matter['id'])
                print(f"[CREATED] {matter_name} -> {new_matter['id']}")
            else:
                print(f"[FAILED] Could not create matter: {matter_name}")

    print()

    # Upload documents
    print("=" * 60)
    print("UPLOADING DOCUMENTS")
    print("=" * 60)
    print()

    results = {
        'success': [],
        'failed': [],
        'processing_failed': []
    }

    for doc in documents:
        doc_id = doc['doc_id']
        title = doc['title']
        doc_type = doc['doc_type']
        doc_date = doc['date']
        file_path = doc.get('file_path')
        bm_matter_id = doc.get('matter_id')

        # Get the API matter ID for this document
        matter_id = matter_id_map.get(bm_matter_id)
        if not matter_id:
            print(f"[SKIP] {doc_id}: No matter mapping for {bm_matter_id}")
            results['failed'].append({'doc_id': doc_id, 'reason': f'No matter mapping for {bm_matter_id}'})
            continue

        if not file_path:
            print(f"[SKIP] {doc_id}: No file path")
            results['failed'].append({'doc_id': doc_id, 'reason': 'No file path'})
            continue

        full_path = script_dir / file_path
        if not full_path.exists():
            print(f"[SKIP] {doc_id}: File not found: {full_path}")
            results['failed'].append({'doc_id': doc_id, 'reason': 'File not found'})
            continue

        # Find matter name for display
        matter_name = next((m['client_name'] for m in benchmark_matters if m['matter_id'] == bm_matter_id), bm_matter_id)

        print(f"[{doc_id}] {title}")
        print(f"    Matter: {matter_name}")
        print(f"    File: {file_path}")
        print(f"    Type: {doc_type}")

        # Upload
        result = client.upload_document(
            file_path=full_path,
            matter_id=matter_id,
            document_type=doc_type,
            document_title=title,
            document_date=doc_date
        )

        if result:
            uploaded_doc_id = result.get('document_id')
            print(f"    Uploaded: {uploaded_doc_id}")

            # Wait for processing
            if not args.skip_processing_wait:
                processing_success = wait_for_processing(client, uploaded_doc_id)
                if processing_success:
                    results['success'].append({
                        'doc_id': doc_id,
                        'document_id': uploaded_doc_id,
                        'matter_id': matter_id,
                        'title': title
                    })
                else:
                    results['processing_failed'].append({
                        'doc_id': doc_id,
                        'document_id': uploaded_doc_id,
                        'matter_id': matter_id,
                        'title': title
                    })
            else:
                results['success'].append({
                    'doc_id': doc_id,
                    'document_id': uploaded_doc_id,
                    'matter_id': matter_id,
                    'title': title
                })
        else:
            results['failed'].append({'doc_id': doc_id, 'reason': 'Upload failed'})

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Matters created/found: {len(matter_id_map)}")
    print(f"  Uploaded successfully: {len(results['success'])}")
    print(f"  Upload failed: {len(results['failed'])}")
    print(f"  Processing failed: {len(results['processing_failed'])}")
    print()

    if results['failed']:
        print("Failed uploads:")
        for item in results['failed']:
            print(f"  - {item['doc_id']}: {item['reason']}")
        print()

    if results['processing_failed']:
        print("Processing failures:")
        for item in results['processing_failed']:
            print(f"  - {item['doc_id']}: {item['document_id']}")
        print()

    # Save results
    results_file = script_dir / "upload_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'matter_id_map': matter_id_map,
            'results': results
        }, f, indent=2)
    print(f"Results saved to: {results_file}")

    # Return exit code
    if results['failed'] or results['processing_failed']:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
