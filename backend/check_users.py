import asyncio
import asyncpg

async def check_users():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/bc_legal_db')
    users = await conn.fetch('SELECT email, is_active FROM users LIMIT 5')
    print('Existing users:')
    for user in users:
        print(f"  - {user['email']} (active: {user['is_active']})")
    await conn.close()

asyncio.run(check_users())
