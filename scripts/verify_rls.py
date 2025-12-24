import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/bc_legal_db")

async def verify_rls():
    print(f"🔌 Connecting to database: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🛠️ Setting up test data...")
        await session.execute(text("SET search_path TO bc_legal_ds, public"))
        
        # Clean up old data to avoid unique constraint conflicts/UUID mismatches
        try:
            await session.execute(text("TRUNCATE companies CASCADE"))
        except Exception as e:
            print(f"Warning during truncate: {e}")
        
        # 1. Create two companies
        company_a_id = uuid.uuid4()
        company_b_id = uuid.uuid4()
        
        # We need to insert as superuser (or bypass RLS) to create companies first
        # For this test, valid RLS depends on the session variable. 
        # If variable is NOT set, and we are superuser, we see everything.
        # If we are strictly checking RLS policies, they usually apply to EVERYONE (FOR ALL) 
        # but often exclude superusers/owners unless FORCE ROW LEVEL SECURITY used.
        # In our SQL script: `FOR ALL TO authenticated_users`.
        # So we likely need to switch role to 'authenticated_users' to test properly.
        
        try:
            # Create companies (bypass RLS by not being restricted user yet, or assuming superuser)
            await session.execute(text("""
                INSERT INTO companies (id, name, subdomain) VALUES (:id, :name, :sub)
                ON CONFLICT DO NOTHING
            """), [{"id": company_a_id, "name": "Company A", "sub": "comp-a"}, 
                   {"id": company_b_id, "name": "Company B", "sub": "comp-b"}])
            
            # Create a document for Company A
            # Create User for Company A
            user_a_id = uuid.uuid4()
            await session.execute(text("""
                INSERT INTO users (id, email, company_id, first_name, last_name) 
                VALUES (:id, :email, :cid, 'User', 'A')
                ON CONFLICT DO NOTHING
            """), {"id": user_a_id, "email": "user@comp-a.com", "cid": company_a_id})

            # Create Matter for Company A
            matter_a_id = uuid.uuid4()
            await session.execute(text("""
                INSERT INTO matters (
                    id, company_id, matter_number, client_name, matter_type, 
                    matter_status, opened_date, created_by, updated_by
                ) VALUES (
                    :id, :cid, 'MAT-001', 'Client A', 'Litigation', 
                    'active', '2023-01-01', :uid, :uid
                )
            """), {"id": matter_a_id, "cid": company_a_id, "uid": user_a_id})
            
            # Create Document for Matter A (includes company_id for RLS)
            doc_a_id = uuid.uuid4()
            await session.execute(text("""
                INSERT INTO documents (
                    id, company_id, matter_id, filename, original_filename, file_extension,
                    file_size_bytes, storage_path, file_hash, document_type,
                    document_title, document_date, document_status, confidentiality_level,
                    created_by, updated_by
                ) VALUES (
                    :id, :cid, :mid, 'secret_a.pdf', 'secret_a.pdf', '.pdf',
                    1024, 's3://bucket/path/to/a', 'hash123', 'pleading',
                    'Secret Pleading', '2023-01-01', 'active', 'standard_confidential',
                    :uid, :uid
                )
            """), {"id": doc_a_id, "cid": company_a_id, "mid": matter_a_id, "uid": user_a_id})
            
            await session.commit()
            print("✅ Test data created.")
            
            # 2. Test Connection AS Company B User (using bc_legal_app role)
            print("\n🕵️ Testing RLS Isolation (acting as Company B)...")
            
            # Reset session to simulate new request
            await session.close()
            
            # Create a new engine as the application user (non-superuser) to properly test RLS
            # Superusers typically bypass RLS
            app_user_url = DATABASE_URL.replace("postgres:postgres", "bc_legal_app:your_secure_password_here")
            app_engine = create_async_engine(app_user_url)
            app_async_session = sessionmaker(app_engine, class_=AsyncSession, expire_on_commit=False)
            
            async with app_async_session() as user_session:
                # Set search path for this user too
                await user_session.execute(text("SET search_path TO bc_legal_ds, public"))
                
                # Set RLS Context for Company B
                # Use set_config function for proper parameter binding
                await user_session.execute(
                    text("SELECT set_config('app.current_company_id', :cid, true)"), 
                    {"cid": str(company_b_id)}
                )
                
                # Try to read Company A's document
                try:
                    result = await user_session.execute(text("SELECT * FROM documents WHERE id = :did"), {"did": doc_a_id})
                    doc = result.fetchone()
                    
                    if doc:
                        print(f"❌ SECURITY FAILURE: Company B could see Company A's document: {doc}")
                    else:
                        print("✅ SECURITY SUCCESS: Company B could NOT see Company A's document.")
                except Exception as e:
                    print(f"Error querying documents: {e}")
                    
            await app_engine.dispose()
                    
                # Verify we can see our own (insert one for B)
                # Note: Insert implies write access, let's just test read isolation first.
                
        except Exception as e:
            print(f"⚠️ Error during verification: {e}")
        finally:
            # Cleanup (as superuser)
            # await session.execute(text("DELETE FROM companies WHERE id IN (:a, :b)"), {"a": company_a_id, "b": company_b_id})
            # await session.commit()
            pass

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_rls())
