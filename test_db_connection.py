"""
Test PostgreSQL Connection to analytics-llm database
Connects to: localhost:5430/analytics-llm
Table: public.sales_analytics
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

# Database connection settings - UPDATE PASSWORD IF DIFFERENT
DB_CONFIG = {
    "host": "localhost",
    "port": 5430,
    "database": "analytics-llm",
    "username": "postgres",
    "password": "root",  # 🔄 CHANGE THIS if your password is different
}

# Build connection URL
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

print(f"🔗 Connecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")


async def test_connection():
    """Test database connection and query sales_analytics table."""
    
    try:
        # Create engine
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )
        
        # Create session
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        async with AsyncSessionLocal() as session:
            # Test 1: Basic connection
            print("\n✅ Step 1: Testing basic connection...")
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"   Connection successful! Query result: {row[0]}")
            
            # Test 2: Check if sales_analytics table exists
            print("\n✅ Step 2: Checking if 'sales_analytics' table exists...")
            table_check = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'sales_analytics'
            """))
            table_exists = table_check.fetchone()
            
            if table_exists:
                print(f"   ✓ Table 'public.sales_analytics' exists!")
            else:
                print("   ⚠️  Table 'sales_analytics' NOT found in public schema")
                
                # List available tables
                print("\n   Available tables in 'public' schema:")
                tables_result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = tables_result.fetchall()
                for t in tables:
                    print(f"   - {t[0]}")
                return
            
            # Test 3: Get table structure
            print("\n✅ Step 3: Getting table structure...")
            columns_result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'sales_analytics'
                ORDER BY ordinal_position
            """))
            columns = columns_result.fetchall()
            
            print(f"\n   📊 Table: public.sales_analytics")
            print(f"   {'Column Name':<30} {'Data Type':<20} {'Nullable'}")
            print(f"   {'-'*30} {'-'*20} {'-'*10}")
            for col in columns:
                print(f"   {col[0]:<30} {col[1]:<20} {col[2]}")
            
            # Test 4: Get row count
            print("\n✅ Step 4: Getting row count...")
            count_result = await session.execute(text(
                "SELECT COUNT(*) FROM public.sales_analytics"
            ))
            row_count = count_result.scalar()
            print(f"   Total rows: {row_count:,}")
            
            # Test 5: Get sample data
            print("\n✅ Step 5: Sample data (first 5 rows)...")
            sample_result = await session.execute(text(
                "SELECT * FROM public.sales_analytics LIMIT 5"
            ))
            sample_rows = sample_result.fetchall()
            column_names = sample_result.keys()
            
            print(f"\n   Columns: {list(column_names)}")
            print(f"\n   Sample rows:")
            for i, row in enumerate(sample_rows, 1):
                print(f"   Row {i}: {dict(zip(column_names, row))}")
            
        # Cleanup
        await engine.dispose()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED! Database connection is working.")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {type(e).__name__}")
        print(f"   {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if password is correct in DB_CONFIG")
        print("   2. Ensure PostgreSQL is running on port 5430")
        print("   3. Verify database name is 'analytics-llm'")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)



