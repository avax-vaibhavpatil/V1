"""Debug script to check stock inventory data and queries"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async def check_stock_data():
    """Check if there's data in stock_gw table"""
    db_url = "postgresql+asyncpg://postgres:root@localhost:5430/new_db"
    engine = create_async_engine(db_url, pool_pre_ping=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    try:
        async with async_session() as session:
            # Check total row count
            result = await session.execute(text("SELECT COUNT(*) FROM stock_gw"))
            total_rows = result.scalar()
            print(f"📊 Total rows in stock_gw: {total_rows}")
            
            # Check date range
            result = await session.execute(text("""
                SELECT 
                    MIN(stgw_date) as min_date,
                    MAX(stgw_date) as max_date,
                    COUNT(DISTINCT stgw_date) as distinct_dates
                FROM stock_gw
            """))
            row = result.fetchone()
            if row:
                print(f"📅 Date range: {row[0]} to {row[1]}")
                print(f"📅 Distinct dates: {row[2]}")
            
            # Check October 2025 data
            result = await session.execute(text("""
                SELECT COUNT(*) 
                FROM stock_gw 
                WHERE EXTRACT(MONTH FROM stgw_date) = 10 
                AND EXTRACT(YEAR FROM stgw_date) = 2025
            """))
            oct_2025_count = result.scalar()
            print(f"📅 October 2025 rows: {oct_2025_count}")
            
            # Check sample data
            result = await session.execute(text("""
                SELECT 
                    branch_name,
                    stgw_date,
                    stgw_val0_3m,
                    stgw_val3_6m,
                    stgw_val6m_1y
                FROM stock_gw
                LIMIT 5
            """))
            print("\n📋 Sample data (first 5 rows):")
            for row in result:
                print(f"  Branch: {row[0]}, Date: {row[1]}, 0-3M: {row[2]}, 3-6M: {row[3]}, 6M-1Y: {row[4]}")
            
            # Check distinct branches
            result = await session.execute(text("SELECT COUNT(DISTINCT branch_name) FROM stock_gw"))
            branch_count = result.scalar()
            print(f"\n🏢 Distinct branches: {branch_count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_stock_data())

