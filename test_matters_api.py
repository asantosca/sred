#!/usr/bin/env python3
"""
Test script for Matters API - BC Legal Tech

This script tests the complete matters management functionality including:
1. Creating a test user and company
2. Authenticating and getting a JWT token
3. Creating, reading, updating, and deleting matters
4. Testing matter access control
"""

import asyncio
import httpx
import json
from datetime import date, datetime
from uuid import uuid4

# API Configuration
API_BASE = "http://localhost:8000/api/v1"
TEST_COMPANY_NAME = "Test Law Firm"
TEST_USER_EMAIL = f"test-{uuid4().hex[:8]}@testlaw.com"
TEST_USER_PASSWORD = "TestPassword123!"

class MattersAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.auth_token = None
        self.user_id = None
        self.company_id = None
        self.created_matter_id = None

    async def setup(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # For now, we'll test with direct database access since auth isn't fully implemented
        # In a real scenario, we'd register a user and get a token
        
        # Create a test user directly in the database
        await self.create_test_user()
        
        print(f"✅ Test user created: {TEST_USER_EMAIL}")

    async def create_test_user(self):
        """Create a test user directly in the database"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from backend.app.db.session import get_db
        from backend.app.models.models import Company, User
        from backend.app.core.security import get_password_hash
        from sqlalchemy import select
        import uuid
        
        # Get database session
        async for db in get_db():
            try:
                # Create company
                company = Company(
                    id=uuid.uuid4(),
                    name=TEST_COMPANY_NAME,
                    is_active=True
                )
                db.add(company)
                await db.flush()
                
                # Create user
                user = User(
                    id=uuid.uuid4(),
                    email=TEST_USER_EMAIL,
                    password_hash=get_password_hash(TEST_USER_PASSWORD),
                    first_name="Test",
                    last_name="User",
                    is_active=True,
                    is_admin=True,
                    company_id=company.id
                )
                db.add(user)
                await db.commit()
                
                self.user_id = str(user.id)
                self.company_id = str(company.id)
                
                print(f"Created company: {company.id}")
                print(f"Created user: {user.id}")
                
            except Exception as e:
                await db.rollback()
                raise e
            break

    async def create_auth_token(self):
        """Create a JWT token for testing"""
        from jose import jwt
        from datetime import datetime, timedelta
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        from backend.app.core.config import settings
        
        # Create JWT payload
        payload = {
            "sub": self.user_id,  # User ID
            "company_id": self.company_id,
            "is_admin": True,
            "permissions": [],
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Create token
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        self.auth_token = token
        print(f"✅ Auth token created")

    def get_headers(self):
        """Get headers with authorization"""
        if not self.auth_token:
            raise ValueError("No auth token available")
        return {"Authorization": f"Bearer {self.auth_token}"}

    async def test_create_matter(self):
        """Test creating a new matter"""
        print("\n📝 Testing matter creation...")
        
        matter_data = {
            "matter_number": f"2024-{uuid4().hex[:6].upper()}",
            "client_name": "ACME Corporation",
            "case_type": "transactional",
            "matter_status": "active",
            "description": "Service agreement review and negotiation",
            "opened_date": date.today().isoformat(),
            "lead_attorney_user_id": self.user_id
        }
        
        response = await self.client.post(
            f"{API_BASE}/matters/",
            json=matter_data,
            headers=self.get_headers()
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            matter = response.json()
            self.created_matter_id = matter["id"]
            print(f"✅ Matter created successfully: {matter['matter_number']}")
            return matter
        else:
            print(f"❌ Failed to create matter: {response.text}")
            return None

    async def test_list_matters(self):
        """Test listing matters"""
        print("\n📋 Testing matter listing...")
        
        response = await self.client.get(
            f"{API_BASE}/matters/",
            headers=self.get_headers()
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            matters_response = response.json()
            print(f"✅ Found {matters_response['total']} matters")
            print(f"Page {matters_response['page']} of {matters_response['pages']}")
            
            for matter in matters_response['matters']:
                print(f"  - {matter['matter_number']}: {matter['client_name']}")
            
            return matters_response
        else:
            print(f"❌ Failed to list matters: {response.text}")
            return None

    async def test_get_matter(self):
        """Test getting a specific matter"""
        if not self.created_matter_id:
            print("⚠️  No matter ID available for testing")
            return None
            
        print(f"\n🔍 Testing matter retrieval for ID: {self.created_matter_id}")
        
        response = await self.client.get(
            f"{API_BASE}/matters/{self.created_matter_id}",
            headers=self.get_headers()
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            matter = response.json()
            print(f"✅ Retrieved matter: {matter['matter_number']}")
            print(f"  Client: {matter['client_name']}")
            print(f"  Status: {matter['matter_status']}")
            return matter
        else:
            print(f"❌ Failed to get matter: {response.text}")
            return None

    async def test_update_matter(self):
        """Test updating a matter"""
        if not self.created_matter_id:
            print("⚠️  No matter ID available for testing")
            return None
            
        print(f"\n✏️  Testing matter update for ID: {self.created_matter_id}")
        
        update_data = {
            "description": "Updated: Service agreement review and negotiation - Priority client",
            "matter_status": "active"
        }
        
        response = await self.client.put(
            f"{API_BASE}/matters/{self.created_matter_id}",
            json=update_data,
            headers=self.get_headers()
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            matter = response.json()
            print(f"✅ Matter updated successfully")
            print(f"  New description: {matter['description']}")
            return matter
        else:
            print(f"❌ Failed to update matter: {response.text}")
            return None

    async def test_matter_access(self):
        """Test matter access management"""
        if not self.created_matter_id:
            print("⚠️  No matter ID available for testing")
            return None
            
        print(f"\n👥 Testing matter access for ID: {self.created_matter_id}")
        
        response = await self.client.get(
            f"{API_BASE}/matters/{self.created_matter_id}/access",
            headers=self.get_headers()
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            access_response = response.json()
            print(f"✅ Retrieved access list for matter: {access_response['matter_number']}")
            print(f"  Users with access: {len(access_response['access_list'])}")
            
            for access in access_response['access_list']:
                print(f"  - {access['user_email']}: {access['access_role']}")
            
            return access_response
        else:
            print(f"❌ Failed to get matter access: {response.text}")
            return None

    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        if self.created_matter_id:
            try:
                response = await self.client.delete(
                    f"{API_BASE}/matters/{self.created_matter_id}",
                    headers=self.get_headers()
                )
                
                if response.status_code == 204:
                    print("✅ Test matter deleted successfully")
                else:
                    print(f"⚠️  Could not delete test matter: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Error deleting test matter: {e}")

        await self.client.aclose()

    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting BC Legal Tech Matters API Tests")
        print("=" * 50)
        
        try:
            await self.setup()
            await self.create_auth_token()
            
            # Run tests
            await self.test_create_matter()
            await self.test_list_matters()
            await self.test_get_matter()
            await self.test_update_matter()
            await self.test_matter_access()
            
            print("\n" + "=" * 50)
            print("🎉 All tests completed!")
            
        except Exception as e:
            print(f"\n💥 Error during testing: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.cleanup()

async def main():
    """Main test function"""
    tester = MattersAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())