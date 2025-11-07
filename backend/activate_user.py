import asyncio
import asyncpg

async def activate_user():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/bc_legal_db')
    await conn.execute(
        "UPDATE users SET is_active = true WHERE email = 'testupload@example.com'"
    )
    print("User activated successfully")
    await conn.close()

asyncio.run(activate_user())
