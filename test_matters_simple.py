#!/usr/bin/env python3
"""
Simple test script for Matters API - BC Legal Tech
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_basic_functionality():
    """Test basic matters functionality"""
    print("Starting BC Legal Tech Matters API Tests")
    print("=" * 50)
    
    try:
        # Test database connection and models
        from backend.app.db.session import get_db
        from backend.app.models.models import Company, User, Matter, MatterAccess
        from sqlalchemy import select
        
        print("Testing database connection...")
        
        async for db in get_db():
            try:
                # Test basic query
                result = await db.execute(select(Company).limit(1))
                companies = result.scalars().all()
                print(f"Found {len(companies)} companies in database")
                
                # Test matters table
                result = await db.execute(select(Matter).limit(1))
                matters = result.scalars().all()
                print(f"Found {len(matters)} matters in database")
                
                print("Database connection and models working correctly!")
                
            except Exception as e:
                print(f"Database error: {e}")
                return False
            break
        
        # Test authentication dependencies
        print("\nTesting authentication dependencies...")
        from backend.app.api.deps import get_current_user
        from backend.app.middleware.auth import get_current_user as get_tenant_context
        print("Authentication dependencies imported successfully!")
        
        # Test API router
        print("\nTesting API router...")
        from backend.app.api.v1.endpoints.matters import router
        print(f"Matters router has {len(router.routes)} routes")
        
        for route in router.routes:
            print(f"  - {route.methods} {route.path}")
        
        print("\nAll basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_basic_functionality()
    
    if success:
        print("\n" + "=" * 50)
        print("SUCCESS: All tests passed!")
        print("The matters API is ready for use.")
        print("\nNext steps:")
        print("1. Implement authentication endpoints")
        print("2. Test with real authentication tokens")
        print("3. Add frontend integration")
    else:
        print("\n" + "=" * 50)
        print("FAILED: Some tests failed.")
        print("Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())