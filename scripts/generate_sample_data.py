"""Script to generate sample data for testing Analytics Studio."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base, get_db
from app.core.config import get_settings
from app.models.project import Project
from app.models.dataset import Dataset, DatasetVersion
from app.models.semantic import SemanticDefinition, SemanticVersion
from app.models.dashboard import Dashboard, DashboardVisual
from app.models.calculation import CalculatedMeasure, MeasureVersion
from datetime import datetime

settings = get_settings()


async def generate_sample_data():
    """Generate sample data for testing."""
    # Create engine and session
    engine = create_async_engine(settings.database_url.replace("+asyncpg", ""))
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("🚀 Generating sample data...\n")

            # 1. Create Projects
            print("📁 Creating projects...")
            project1 = Project(
                name="Sales Analytics",
                description="Sales team analytics workspace",
                created_by="admin",
            )
            project2 = Project(
                name="Marketing Analytics",
                description="Marketing team analytics workspace",
                created_by="admin",
            )
            session.add(project1)
            session.add(project2)
            await session.flush()
            print(f"   ✅ Created project: {project1.name} (ID: {project1.id})")
            print(f"   ✅ Created project: {project2.name} (ID: {project2.id})\n")

            # 2. Create Datasets
            print("📊 Creating datasets...")
            dataset1 = Dataset(
                id="sales_data",
                project_id=project1.id,
                name="Sales Data",
                description="Daily sales transactions",
                table_name="sales_fact",
                grain="daily",
                source_type="sql",
                created_by="admin",
            )
            dataset2 = Dataset(
                id="customer_data",
                project_id=project1.id,
                name="Customer Data",
                description="Customer demographics and segments",
                table_name="customers",
                grain="daily",
                source_type="sql",
                created_by="admin",
            )
            dataset3 = Dataset(
                id="campaign_data",
                project_id=project2.id,
                name="Campaign Data",
                description="Marketing campaign performance",
                table_name="campaigns",
                grain="daily",
                source_type="sql",
                created_by="admin",
            )

            session.add(dataset1)
            session.add(dataset2)
            session.add(dataset3)
            await session.flush()
            print(f"   ✅ Created dataset: {dataset1.name} (ID: {dataset1.id})")
            print(f"   ✅ Created dataset: {dataset2.name} (ID: {dataset2.id})")
            print(f"   ✅ Created dataset: {dataset3.name} (ID: {dataset3.id})\n")

            # Create dataset versions
            version1 = DatasetVersion(
                dataset_id=dataset1.id,
                version=1,
                is_current=True,
                created_by="admin",
            )
            session.add(version1)

            # 3. Create Semantic Definitions
            print("🔍 Creating semantic definitions...")
            semantic1 = SemanticDefinition(
                dataset_id=dataset1.id,
                name="Sales Semantic Layer",
                description="Semantic layer for sales data",
                created_by="admin",
            )
            session.add(semantic1)
            await session.flush()

            semantic_version1 = SemanticVersion(
                semantic_definition_id=semantic1.id,
                version=1,
                schema_json={
                    "grain": "daily",
                    "time_columns": ["sale_date", "created_at"],
                    "dimensions": [
                        {
                            "name": "region",
                            "column": "region_name",
                            "type": "string",
                            "description": "Geographic region",
                        },
                        {
                            "name": "product_category",
                            "column": "category",
                            "type": "string",
                            "description": "Product category",
                        },
                        {
                            "name": "customer_segment",
                            "column": "segment",
                            "type": "string",
                            "description": "Customer segment",
                        },
                    ],
                    "measures": [
                        {
                            "name": "revenue",
                            "column": "amount",
                            "type": "numeric",
                            "aggregations": ["SUM", "AVG", "MIN", "MAX"],
                            "format": "currency",
                            "description": "Sales revenue",
                        },
                        {
                            "name": "quantity",
                            "column": "qty",
                            "type": "numeric",
                            "aggregations": ["SUM", "AVG", "COUNT"],
                            "description": "Quantity sold",
                        },
                        {
                            "name": "order_count",
                            "column": "order_id",
                            "type": "numeric",
                            "aggregations": ["COUNT", "DISTINCT_COUNT"],
                            "description": "Number of orders",
                        },
                    ],
                },
                is_current=True,
                created_by="admin",
            )
            session.add(semantic_version1)
            print(f"   ✅ Created semantic definition for {dataset1.name}\n")

            # 4. Create Calculated Measures
            print("🧮 Creating calculated measures...")
            measure1 = CalculatedMeasure(
                dataset_id=dataset1.id,
                name="Profit Margin",
                description="Revenue minus cost divided by revenue",
                created_by="admin",
            )
            session.add(measure1)
            await session.flush()

            measure_version1 = MeasureVersion(
                measure_id=measure1.id,
                version=1,
                formula="(revenue - cost) / revenue * 100",
                is_current=True,
                is_valid=True,
                created_by="admin",
            )
            session.add(measure_version1)
            print(f"   ✅ Created calculated measure: {measure1.name}\n")

            # 5. Create Dashboards
            print("📈 Creating dashboards...")
            dashboard1 = Dashboard(
                project_id=project1.id,
                name="Sales Overview",
                description="Key sales metrics and trends",
                layout_config={"columns": 12, "rows": 8, "cell_height": 100},
                is_public=False,
                created_by="admin",
            )
            session.add(dashboard1)
            await session.flush()

            # Add visuals to dashboard
            visual1 = DashboardVisual(
                dashboard_id=dashboard1.id,
                visual_type="kpi",
                visual_config={
                    "measure": {
                        "name": "revenue",
                        "column": "amount",
                        "aggregation": "SUM",
                        "alias": "total_revenue",
                    },
                    "filters": [],
                    "time_filter": {
                        "column": "sale_date",
                        "start_date": "2024-01-01",
                        "end_date": "2024-12-31",
                    },
                },
                position={"x": 0, "y": 0, "width": 3, "height": 2},
                order=0,
            )

            visual2 = DashboardVisual(
                dashboard_id=dashboard1.id,
                visual_type="bar",
                visual_config={
                    "dimensions": ["region"],
                    "measures": [
                        {
                            "name": "revenue",
                            "column": "amount",
                            "aggregation": "SUM",
                            "alias": "revenue_by_region",
                        }
                    ],
                    "filters": [],
                    "time_filter": {
                        "column": "sale_date",
                        "start_date": "2024-01-01",
                        "end_date": "2024-12-31",
                    },
                    "sorting": {"field": "revenue_by_region", "order": "desc"},
                },
                position={"x": 3, "y": 0, "width": 9, "height": 4},
                order=1,
            )

            session.add(visual1)
            session.add(visual2)

            dashboard2 = Dashboard(
                project_id=project2.id,
                name="Campaign Performance",
                description="Marketing campaign analytics",
                layout_config={"columns": 12, "rows": 6, "cell_height": 100},
                is_public=False,
                created_by="admin",
            )
            session.add(dashboard2)

            print(f"   ✅ Created dashboard: {dashboard1.name} (ID: {dashboard1.id})")
            print(f"   ✅ Created dashboard: {dashboard2.name} (ID: {dashboard2.id})\n")

            # Commit all changes
            await session.commit()
            print("✅ All sample data generated successfully!\n")

            # Print summary
            print("📋 Summary:")
            print(f"   Projects: 2")
            print(f"   Datasets: 3")
            print(f"   Semantic Definitions: 1")
            print(f"   Calculated Measures: 1")
            print(f"   Dashboards: 2")
            print(f"   Dashboard Visuals: 2\n")

            print("🎯 Test the API:")
            print(f"   GET /api/v1/projects")
            print(f"   GET /api/v1/datasets?project_id={project1.id}")
            print(f"   GET /api/v1/dashboards?project_id={project1.id}")
            print(f"   GET /api/v1/datasets/{dataset1.id}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error generating sample data: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(generate_sample_data())

