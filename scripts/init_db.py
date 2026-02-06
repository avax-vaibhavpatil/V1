"""Initialize database with all tables."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models to register them
from app.models import *  # noqa: F401, F403
from app.core.database import init_db

async def main():
    print("🗄️  Initializing database...")
    await init_db()
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())

