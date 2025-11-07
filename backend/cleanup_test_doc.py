import asyncio
import asyncpg

async def cleanup():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/bc_legal_db')
    # Delete the test document
    result = await conn.execute(
        "DELETE FROM documents WHERE document_title = 'Employment Agreement - Embedding Test'"
    )
    print(f"Deleted test document: {result}")
    await conn.close()

asyncio.run(cleanup())
