"""
Reports API - Sales Analytics Endpoints

Provides API endpoints for the sales analytics dashboard.
Connects to PostgreSQL database (analytics-llm) for real data.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# ============================================
# Database Connection - analytics-llm
# ============================================

# Connection to the analytics_llm PostgreSQL database (uses .env config)
ANALYTICS_DB_URL = settings.database_url

analytics_engine = create_async_engine(
    ANALYTICS_DB_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

AnalyticsSessionLocal = async_sessionmaker(
    analytics_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_analytics_db():
    """Get analytics database session."""
    async with AnalyticsSessionLocal() as session:
        yield session


# ============================================
# Request/Response Models
# ============================================

class FilterState(BaseModel):
    itemGroup: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    customerState: Optional[List[str]] = None
    industry: Optional[List[str]] = None
    customerCategory: Optional[str] = None
    customerType: Optional[str] = None
    period: Optional[str] = None


class TimeState(BaseModel):
    fiscalYear: str = "2025-2026"
    period: str = "January 2026"


class ToggleState(BaseModel):
    aggregation: str = "YTD"
    metricMode: str = "VALUE"


class PaginationParams(BaseModel):
    page: int = 1
    pageSize: int = 50


class SortParams(BaseModel):
    key: str = "overall_actualSales"
    direction: str = "desc"


class KpisRequest(BaseModel):
    filters: FilterState = FilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()


class TableRequest(BaseModel):
    filters: FilterState = FilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()
    pagination: PaginationParams = PaginationParams()
    sort: SortParams = SortParams()
    search: Optional[str] = None
    entityViewMode: str = "groupheadname"


class DrilldownRequest(BaseModel):
    entityId: str
    entityColumn: str = "groupheadname"
    filters: FilterState = FilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()


# ============================================
# Helper Functions
# ============================================

# Fiscal year periods in order (April to March)
FISCAL_YEAR_PERIODS = [
    "April", "May", "June", "July", "August", "September",
    "October", "November", "December", "January", "February", "March"
]

# Fiscal quarters
FISCAL_QUARTERS = {
    "Q1": ["April", "May", "June"],
    "Q2": ["July", "August", "September"],
    "Q3": ["October", "November", "December"],
    "Q4": ["January", "February", "March"]
}

def get_period_month(period: str) -> str:
    """Extract month name from period string like 'January 2026'."""
    return period.split()[0] if period else ""

def get_period_year(period: str) -> str:
    """Extract year from period string like 'January 2026'."""
    parts = period.split()
    return parts[1] if len(parts) > 1 else ""

def get_fiscal_quarter(month: str) -> str:
    """Get fiscal quarter for a given month."""
    for quarter, months in FISCAL_QUARTERS.items():
        if month in months:
            return quarter
    return "Q1"

def get_periods_for_aggregation(period: str, aggregation: str) -> list[str]:
    """
    Get list of periods to include based on aggregation type.
    
    - MTD: Just the selected period
    - QTD: All periods in the current fiscal quarter up to selected period
    - YTD: All periods from fiscal year start to selected period
    """
    if not period:
        return []
    
    month = get_period_month(period)
    year = get_period_year(period)
    
    if aggregation == "MTD":
        # Month to Date - just this period
        return [period]
    
    # Determine the year for each month in fiscal year
    # FY 2025-2026: April 2025 - March 2026
    # April-December use first year, January-March use second year
    fy_start_year = int(year) if month in ["April", "May", "June", "July", "August", "September", "October", "November", "December"] else int(year) - 1
    
    if aggregation == "QTD":
        # Quarter to Date - periods in current quarter up to selected period
        quarter = get_fiscal_quarter(month)
        quarter_months = FISCAL_QUARTERS[quarter]
        
        periods = []
        for m in quarter_months:
            # Determine year for this month
            if m in ["January", "February", "March"]:
                m_year = str(fy_start_year + 1)
            else:
                m_year = str(fy_start_year)
            
            period_str = f"{m} {m_year}"
            periods.append(period_str)
            
            # Stop at the selected month
            if m == month:
                break
        
        return periods
    
    elif aggregation == "YTD":
        # Year to Date - all periods from fiscal year start to selected period
        periods = []
        
        for m in FISCAL_YEAR_PERIODS:
            # Determine year for this month
            if m in ["January", "February", "March"]:
                m_year = str(fy_start_year + 1)
            else:
                m_year = str(fy_start_year)
            
            period_str = f"{m} {m_year}"
            periods.append(period_str)
            
            # Stop at the selected month
            if m == month:
                break
        
        return periods
    
    # Default to just the selected period
    return [period]


def build_filter_clause(filters: FilterState, time: TimeState, aggregation: str = "MTD") -> tuple[str, dict]:
    """Build SQL WHERE clause from filters."""
    clauses = []
    params = {}
    
    # Period filter based on aggregation
    if time.period:
        periods = get_periods_for_aggregation(time.period, aggregation)
        if len(periods) == 1:
            clauses.append("period = :period")
            params["period"] = periods[0]
        elif len(periods) > 1:
            placeholders = ", ".join([f":period_{i}" for i in range(len(periods))])
            clauses.append(f"period IN ({placeholders})")
            for i, p in enumerate(periods):
                params[f"period_{i}"] = p
    
    # Item Group filter
    if filters.itemGroup and filters.itemGroup != "ALL":
        if filters.itemGroup.endswith('%'):
            clauses.append("itemgroup LIKE :itemGroup")
        else:
            clauses.append("itemgroup = :itemGroup")
        params["itemGroup"] = filters.itemGroup
    
    # Material filter
    if filters.material and filters.material != "ALL":
        clauses.append("material = :material")
        params["material"] = filters.material
    
    # Brand filter
    if filters.brand and filters.brand != "ALL":
        clauses.append("brand = :brand")
        params["brand"] = filters.brand
    
    # Customer State filter (multi-select)
    if filters.customerState and len(filters.customerState) > 0:
        placeholders = ", ".join([f":state_{i}" for i in range(len(filters.customerState))])
        clauses.append(f"customer_state IN ({placeholders})")
        for i, state in enumerate(filters.customerState):
            params[f"state_{i}"] = state
    
    # Industry filter (multi-select)
    if filters.industry and len(filters.industry) > 0:
        placeholders = ", ".join([f":industry_{i}" for i in range(len(filters.industry))])
        clauses.append(f"industry IN ({placeholders})")
        for i, ind in enumerate(filters.industry):
            params[f"industry_{i}"] = ind
    
    # Customer Category filter
    if filters.customerCategory and filters.customerCategory != "ALL":
        clauses.append("customer_category = :customerCategory")
        params["customerCategory"] = filters.customerCategory
    
    # Customer Type filter
    if filters.customerType and filters.customerType != "ALL":
        clauses.append("customer_type = :customerType")
        params["customerType"] = filters.customerType
    
    where_clause = " AND ".join(clauses) if clauses else "1=1"
    return where_clause, params


# ============================================
# API Endpoints
# ============================================

@router.get("/sales-analytics/meta")
async def get_report_meta():
    """Get report metadata including last updated time and feature flags."""
    async with AnalyticsSessionLocal() as session:
        try:
            # Get last updated from max date in data
            result = await session.execute(text(
                "SELECT MAX(asondate) as last_date FROM sales_analytics"
            ))
            row = result.fetchone()
            last_date = row[0] if row else datetime.now().date()
            
            return {
                "lastUpdatedAt": str(last_date),
                "features": {
                    "export": True,
                    "drilldown": True,
                    "share": True,
                    "refresh": True,
                    "print": True,
                    "columnToggle": True,
                    "viewModeSwitch": True,
                },
                "allowed": {
                    "periods": await get_distinct_values(session, "period"),
                    "states": await get_distinct_values(session, "customer_state"),
                    "industries": await get_distinct_values(session, "industry"),
                    "brands": await get_distinct_values(session, "brand"),
                }
            }
        except Exception as e:
            logger.error(f"Error fetching meta: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def get_distinct_values(session: AsyncSession, column: str) -> List[str]:
    """Get distinct non-null values from a column."""
    result = await session.execute(text(
        f"SELECT DISTINCT {column} FROM sales_analytics WHERE {column} IS NOT NULL ORDER BY {column}"
    ))
    return [row[0] for row in result.fetchall()]


@router.post("/sales-analytics/kpis")
async def get_report_kpis(request: KpisRequest):
    """Get aggregated KPI data for the summary cards."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_filter_clause(request.filters, request.time, request.toggles.aggregation)
            
            query = text(f"""
                SELECT 
                    -- Building Wires
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleamt_ason ELSE 0 END), 0) as buildingwires_sales,
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN profitloss_ason ELSE 0 END), 0) as buildingwires_profit,
                    
                    -- LT Cables
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleamt_ason ELSE 0 END), 0) as ltcables_sales,
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN profitloss_ason ELSE 0 END), 0) as ltcables_profit,
                    
                    -- Flexibles
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleamt_ason ELSE 0 END), 0) as flexibles_sales,
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN profitloss_ason ELSE 0 END), 0) as flexibles_profit,
                    
                    -- HT & EHV
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleamt_ason ELSE 0 END), 0) as htehv_sales,
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN profitloss_ason ELSE 0 END), 0) as htehv_profit,
                    
                    -- Overall
                    COALESCE(SUM(saleamt_ason), 0) as total_sales,
                    COALESCE(SUM(profitloss_ason), 0) as total_profit,
                    COALESCE(SUM(metalweightsold_ason), 0) as total_weight
                    
                FROM sales_analytics
                WHERE {where_clause}
            """)
            
            result = await session.execute(query, params)
            row_tuple = result.fetchone()
            
            if not row_tuple:
                return {"cards": []}
            
            # Convert to dict using column names from result keys
            columns = result.keys()
            row = dict(zip(columns, row_tuple))
            
            total_sales = float(row.get('total_sales', 0) or 0)
            
            # Calculate contribution percentages
            def calc_contribution(sales):
                return round((float(sales) / total_sales * 100) if total_sales > 0 else 0, 1)
            
            def calc_margin(sales, profit):
                s = float(sales) if sales else 0
                p = float(profit) if profit else 0
                return round((p / s * 100) if s > 0 else 0, 1)
            
            bw_sales = float(row.get('buildingwires_sales', 0) or 0)
            bw_profit = float(row.get('buildingwires_profit', 0) or 0)
            lt_sales = float(row.get('ltcables_sales', 0) or 0)
            lt_profit = float(row.get('ltcables_profit', 0) or 0)
            flex_sales = float(row.get('flexibles_sales', 0) or 0)
            flex_profit = float(row.get('flexibles_profit', 0) or 0)
            ht_sales = float(row.get('htehv_sales', 0) or 0)
            ht_profit = float(row.get('htehv_profit', 0) or 0)
            total_profit = float(row.get('total_profit', 0) or 0)
            total_weight = float(row.get('total_weight', 0) or 0)
            
            cards = [
                {
                    "id": "buildingWires",
                    "actualSales": bw_sales,
                    "profitLoss": bw_profit,
                    "contributionPct": calc_contribution(bw_sales),
                    "marginPct": calc_margin(bw_sales, bw_profit),
                },
                {
                    "id": "ltCables",
                    "actualSales": lt_sales,
                    "profitLoss": lt_profit,
                    "contributionPct": calc_contribution(lt_sales),
                    "marginPct": calc_margin(lt_sales, lt_profit),
                },
                {
                    "id": "flexibles",
                    "actualSales": flex_sales,
                    "profitLoss": flex_profit,
                    "contributionPct": calc_contribution(flex_sales),
                    "marginPct": calc_margin(flex_sales, flex_profit),
                },
                {
                    "id": "htEhv",
                    "actualSales": ht_sales,
                    "profitLoss": ht_profit,
                    "contributionPct": calc_contribution(ht_sales),
                    "marginPct": calc_margin(ht_sales, ht_profit),
                },
                {
                    "id": "overall",
                    "actualSales": total_sales,
                    "profitLoss": total_profit,
                    "contributionPct": 100.0,
                    "marginPct": calc_margin(total_sales, total_profit),
                    "metalWeight": total_weight,
                },
            ]
            
            return {"cards": cards}
            
        except Exception as e:
            logger.error(f"Error fetching KPIs: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales-analytics/table")
async def get_report_table(request: TableRequest):
    """Get paginated table data with filtering, sorting, and search."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_filter_clause(request.filters, request.time, request.toggles.aggregation)
            entity_column = request.entityViewMode or "groupheadname"
            
            # Map sort keys to SQL expressions
            sort_key = request.sort.key
            sort_dir = request.sort.direction.upper()
            if sort_dir not in ("ASC", "DESC"):
                sort_dir = "DESC"
            
            # Build search clause
            search_clause = ""
            if request.search:
                search_clause = f"AND {entity_column} ILIKE :search"
                params["search"] = f"%{request.search}%"
            
            # Get total count first
            count_query = text(f"""
                SELECT COUNT(DISTINCT {entity_column}) as total
                FROM sales_analytics
                WHERE {where_clause} {search_clause}
                AND {entity_column} IS NOT NULL
            """)
            count_result = await session.execute(count_query, params)
            total = count_result.scalar() or 0
            
            # Calculate pagination
            offset = (request.pagination.page - 1) * request.pagination.pageSize
            params["limit"] = request.pagination.pageSize
            params["offset"] = offset
            
            # Main data query - include regionalheadname for display
            query = text(f"""
                SELECT 
                    {entity_column} as entity_name,
                    MAX(regionalheadname) as regional_head,
                    
                    -- Building Wires
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleamt_ason ELSE 0 END), 0) as "buildingWires_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN profitloss_ason ELSE 0 END), 0) as "buildingWires_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleqty_ason ELSE 0 END), 0) as "buildingWires_qty",
                    
                    -- LT Cables
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleamt_ason ELSE 0 END), 0) as "ltCables_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN profitloss_ason ELSE 0 END), 0) as "ltCables_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleqty_ason ELSE 0 END), 0) as "ltCables_qty",
                    
                    -- Flexibles
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleamt_ason ELSE 0 END), 0) as "flexibles_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN profitloss_ason ELSE 0 END), 0) as "flexibles_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleqty_ason ELSE 0 END), 0) as "flexibles_qty",
                    
                    -- HT & EHV
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleamt_ason ELSE 0 END), 0) as "htEhv_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN profitloss_ason ELSE 0 END), 0) as "htEhv_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleqty_ason ELSE 0 END), 0) as "htEhv_qty",
                    
                    -- Overall
                    COALESCE(SUM(saleamt_ason), 0) as "overall_actualSales",
                    COALESCE(SUM(profitloss_ason), 0) as "overall_profitLoss",
                    COALESCE(SUM(saleqty_ason), 0) as "overall_qty",
                    COALESCE(SUM(metalweightsold_ason), 0) as "overall_metalWeight",
                    COALESCE(SUM(item_receivable), 0) as "overall_receivables"
                    
                FROM sales_analytics
                WHERE {where_clause} {search_clause}
                AND {entity_column} IS NOT NULL
                GROUP BY {entity_column}
                HAVING SUM(saleamt_ason) > 0
                ORDER BY "overall_actualSales" {sort_dir}
                LIMIT :limit OFFSET :offset
            """)
            
            result = await session.execute(query, params)
            rows_data = result.fetchall()
            column_names = result.keys()
            
            # Convert to list of dicts and calculate margins
            rows = []
            for i, row in enumerate(rows_data):
                row_dict = dict(zip(column_names, row))
                entity_name = row_dict.get("entity_name", f"Entity_{i}")
                regional_head = row_dict.get("regional_head", "")
                
                # Calculate margins for each category
                def calc_margin(sales_key, pl_key):
                    sales = float(row_dict.get(sales_key, 0) or 0)
                    pl = float(row_dict.get(pl_key, 0) or 0)
                    return round((pl / sales * 100) if sales > 0 else 0, 1)
                
                rows.append({
                    "entityId": str(entity_name).replace(" ", "_").lower()[:50],
                    "entityName": entity_name,
                    "entityCode": "",
                    "regionalHead": regional_head or "",
                    
                    # Building Wires
                    "buildingWires_actualSales": float(row_dict.get("buildingWires_actualSales", 0) or 0),
                    "buildingWires_profitLoss": float(row_dict.get("buildingWires_profitLoss", 0) or 0),
                    "buildingWires_qty": float(row_dict.get("buildingWires_qty", 0) or 0),
                    "buildingWires_margin": calc_margin("buildingWires_actualSales", "buildingWires_profitLoss"),
                    
                    # LT Cables
                    "ltCables_actualSales": float(row_dict.get("ltCables_actualSales", 0) or 0),
                    "ltCables_profitLoss": float(row_dict.get("ltCables_profitLoss", 0) or 0),
                    "ltCables_qty": float(row_dict.get("ltCables_qty", 0) or 0),
                    "ltCables_margin": calc_margin("ltCables_actualSales", "ltCables_profitLoss"),
                    
                    # Flexibles
                    "flexibles_actualSales": float(row_dict.get("flexibles_actualSales", 0) or 0),
                    "flexibles_profitLoss": float(row_dict.get("flexibles_profitLoss", 0) or 0),
                    "flexibles_qty": float(row_dict.get("flexibles_qty", 0) or 0),
                    "flexibles_margin": calc_margin("flexibles_actualSales", "flexibles_profitLoss"),
                    
                    # HT & EHV
                    "htEhv_actualSales": float(row_dict.get("htEhv_actualSales", 0) or 0),
                    "htEhv_profitLoss": float(row_dict.get("htEhv_profitLoss", 0) or 0),
                    "htEhv_qty": float(row_dict.get("htEhv_qty", 0) or 0),
                    "htEhv_margin": calc_margin("htEhv_actualSales", "htEhv_profitLoss"),
                    
                    # Overall
                    "overall_actualSales": float(row_dict.get("overall_actualSales", 0) or 0),
                    "overall_profitLoss": float(row_dict.get("overall_profitLoss", 0) or 0),
                    "overall_qty": float(row_dict.get("overall_qty", 0) or 0),
                    "overall_metalWeight": float(row_dict.get("overall_metalWeight", 0) or 0),
                    "overall_receivables": float(row_dict.get("overall_receivables", 0) or 0),
                    "overall_margin": calc_margin("overall_actualSales", "overall_profitLoss"),
                })
            
            # Get summary row (totals)
            summary_query = text(f"""
                SELECT 
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleamt_ason ELSE 0 END), 0) as "buildingWires_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN profitloss_ason ELSE 0 END), 0) as "buildingWires_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleqty_ason ELSE 0 END), 0) as "buildingWires_qty",
                    
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleamt_ason ELSE 0 END), 0) as "ltCables_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN profitloss_ason ELSE 0 END), 0) as "ltCables_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleqty_ason ELSE 0 END), 0) as "ltCables_qty",
                    
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleamt_ason ELSE 0 END), 0) as "flexibles_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN profitloss_ason ELSE 0 END), 0) as "flexibles_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleqty_ason ELSE 0 END), 0) as "flexibles_qty",
                    
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleamt_ason ELSE 0 END), 0) as "htEhv_actualSales",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN profitloss_ason ELSE 0 END), 0) as "htEhv_profitLoss",
                    COALESCE(SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleqty_ason ELSE 0 END), 0) as "htEhv_qty",
                    
                    COALESCE(SUM(saleamt_ason), 0) as "overall_actualSales",
                    COALESCE(SUM(profitloss_ason), 0) as "overall_profitLoss",
                    COALESCE(SUM(saleqty_ason), 0) as "overall_qty",
                    COALESCE(SUM(metalweightsold_ason), 0) as "overall_metalWeight",
                    COALESCE(SUM(item_receivable), 0) as "overall_receivables"
                FROM sales_analytics
                WHERE {where_clause}
            """)
            
            summary_result = await session.execute(summary_query, {k: v for k, v in params.items() if k not in ["limit", "offset", "search"]})
            summary_row = summary_result.fetchone()
            
            summary = None
            if summary_row:
                summary_dict = dict(zip(summary_result.keys(), summary_row))
                
                def calc_margin(sales_key, pl_key):
                    sales = float(summary_dict.get(sales_key, 0) or 0)
                    pl = float(summary_dict.get(pl_key, 0) or 0)
                    return round((pl / sales * 100) if sales > 0 else 0, 1)
                
                summary = {
                    "entityId": "total",
                    "entityName": "TOTAL",
                    "buildingWires_actualSales": float(summary_dict.get("buildingWires_actualSales", 0) or 0),
                    "buildingWires_profitLoss": float(summary_dict.get("buildingWires_profitLoss", 0) or 0),
                    "buildingWires_qty": float(summary_dict.get("buildingWires_qty", 0) or 0),
                    "buildingWires_margin": calc_margin("buildingWires_actualSales", "buildingWires_profitLoss"),
                    "ltCables_actualSales": float(summary_dict.get("ltCables_actualSales", 0) or 0),
                    "ltCables_profitLoss": float(summary_dict.get("ltCables_profitLoss", 0) or 0),
                    "ltCables_qty": float(summary_dict.get("ltCables_qty", 0) or 0),
                    "ltCables_margin": calc_margin("ltCables_actualSales", "ltCables_profitLoss"),
                    "flexibles_actualSales": float(summary_dict.get("flexibles_actualSales", 0) or 0),
                    "flexibles_profitLoss": float(summary_dict.get("flexibles_profitLoss", 0) or 0),
                    "flexibles_qty": float(summary_dict.get("flexibles_qty", 0) or 0),
                    "flexibles_margin": calc_margin("flexibles_actualSales", "flexibles_profitLoss"),
                    "htEhv_actualSales": float(summary_dict.get("htEhv_actualSales", 0) or 0),
                    "htEhv_profitLoss": float(summary_dict.get("htEhv_profitLoss", 0) or 0),
                    "htEhv_qty": float(summary_dict.get("htEhv_qty", 0) or 0),
                    "htEhv_margin": calc_margin("htEhv_actualSales", "htEhv_profitLoss"),
                    "overall_actualSales": float(summary_dict.get("overall_actualSales", 0) or 0),
                    "overall_profitLoss": float(summary_dict.get("overall_profitLoss", 0) or 0),
                    "overall_qty": float(summary_dict.get("overall_qty", 0) or 0),
                    "overall_metalWeight": float(summary_dict.get("overall_metalWeight", 0) or 0),
                    "overall_receivables": float(summary_dict.get("overall_receivables", 0) or 0),
                    "overall_margin": calc_margin("overall_actualSales", "overall_profitLoss"),
                }
            
            return {
                "rows": rows,
                "page": request.pagination.page,
                "pageSize": request.pagination.pageSize,
                "total": total,
                "summary": summary,
            }
            
        except Exception as e:
            logger.error(f"Error fetching table data: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales-analytics/drilldown")
async def get_report_drilldown(request: DrilldownRequest):
    """Get detailed drilldown data for a specific entity."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_filter_clause(request.filters, request.time, request.toggles.aggregation)
            entity_column = request.entityColumn or "groupheadname"
            
            # Add entity filter - use ILIKE for case-insensitive match
            entity_clause = f"AND LOWER({entity_column}) = LOWER(:entity_id)"
            params["entity_id"] = request.entityId.replace("_", " ")
            
            # Get summary data
            summary_query = text(f"""
                SELECT 
                    COALESCE(SUM(saleamt_ason), 0) as total_sales,
                    COALESCE(SUM(profitloss_ason), 0) as total_profit,
                    COALESCE(SUM(saleqty_ason), 0) as total_qty,
                    COALESCE(SUM(metalweightsold_ason), 0) as total_weight,
                    COALESCE(SUM(item_receivable), 0) as total_receivables
                FROM sales_analytics
                WHERE {where_clause} {entity_clause}
            """)
            
            summary_result = await session.execute(summary_query, params)
            summary_row = summary_result.fetchone()
            
            # Get trend data by period
            trend_query = text(f"""
                SELECT 
                    period,
                    COALESCE(SUM(saleamt_ason), 0) as sales
                FROM sales_analytics
                WHERE LOWER({entity_column}) = LOWER(:entity_id)
                AND {entity_column} IS NOT NULL
                GROUP BY period
                ORDER BY period
            """)
            
            trend_result = await session.execute(trend_query, {"entity_id": params["entity_id"]})
            trend_data = [
                {"period": row[0], "value": float(row[1])}
                for row in trend_result.fetchall()
            ]
            
            # Get breakdown by item group
            breakdown_query = text(f"""
                SELECT 
                    itemgroup,
                    COALESCE(SUM(saleamt_ason), 0) as sales
                FROM sales_analytics
                WHERE {where_clause} {entity_clause}
                AND itemgroup IS NOT NULL
                GROUP BY itemgroup
                ORDER BY sales DESC
                LIMIT 10
            """)
            
            breakdown_result = await session.execute(breakdown_query, params)
            breakdown_rows = breakdown_result.fetchall()
            
            total_sales = sum(float(row[1]) for row in breakdown_rows) or 1
            breakdown_data = [
                {
                    "name": row[0],
                    "value": float(row[1]),
                    "percentage": round(float(row[1]) / total_sales * 100, 1),
                }
                for row in breakdown_rows
            ]
            
            return {
                "entity": {
                    "id": request.entityId,
                    "name": params["entity_id"],
                    "code": "",
                },
                "summary": {
                    "actualSales": float(summary_row[0]) if summary_row else 0,
                    "profitLoss": float(summary_row[1]) if summary_row else 0,
                    "quantity": float(summary_row[2]) if summary_row else 0,
                    "metalWeight": float(summary_row[3]) if summary_row else 0,
                    "receivables": float(summary_row[4]) if summary_row else 0,
                },
                "trend": trend_data,
                "breakdown": {
                    "byCategory": breakdown_data,
                },
            }
            
        except Exception as e:
            logger.error(f"Error fetching drilldown: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales-analytics/export")
async def export_report(request: TableRequest):
    """Export report data as CSV."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_filter_clause(request.filters, request.time, request.toggles.aggregation)
            entity_column = request.entityViewMode or "groupheadname"
            
            # Get all data without pagination
            query = text(f"""
                SELECT 
                    {entity_column} as entity_name,
                    COALESCE(SUM(saleamt_ason), 0) as total_sales,
                    COALESCE(SUM(profitloss_ason), 0) as total_profit,
                    COALESCE(SUM(saleqty_ason), 0) as total_qty,
                    COALESCE(SUM(metalweightsold_ason), 0) as total_weight,
                    COALESCE(SUM(item_receivable), 0) as total_receivables
                FROM sales_analytics
                WHERE {where_clause}
                AND {entity_column} IS NOT NULL
                GROUP BY {entity_column}
                HAVING SUM(saleamt_ason) > 0
                ORDER BY total_sales DESC
            """)
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            
            # Generate CSV
            csv_lines = ["Entity,Total Sales,Total Profit,Total Qty,Metal Weight,Receivables"]
            for row in rows:
                csv_lines.append(f'"{row[0]}",{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}')
            
            return {
                "csv": "\n".join(csv_lines),
                "filename": f"sales_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            }
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AI Chat Endpoint
# ============================================

class ChatRequest(BaseModel):
    """Request model for AI chat."""
    question: str
    filters: Optional[FilterState] = None
    time: Optional[TimeState] = None
    includeSql: bool = True
    includeData: bool = False  # Default false to reduce response size


class ChatMessageResponse(BaseModel):
    """Response model for AI chat."""
    status: str
    answer: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    rowCount: int = 0
    error: Optional[str] = None
    timing: Dict[str, int] = {}
    usage: Dict[str, Any] = {}


@router.post("/sales-analytics/chat")
async def chat_with_report(request: ChatRequest):
    """
    AI-powered chat endpoint for natural language queries.
    
    Ask questions in natural language and get answers based on the data.
    
    Examples:
    - "Top 5 customers in Gujarat"
    - "Total sales of building wires"
    - "Who has negative margin?"
    - "Compare building wires vs LT cables"
    - "Monthly sales trend"
    """
    from app.services.chat_service import get_chat_service
    
    try:
        chat_service = get_chat_service()
        
        # Convert filters to dict format for chat service
        filters_dict = None
        if request.filters or request.time:
            filters_dict = {}
            
            if request.filters:
                if request.filters.itemGroup and request.filters.itemGroup != "ALL":
                    filters_dict["itemGroup"] = request.filters.itemGroup
                if request.filters.material and request.filters.material != "ALL":
                    filters_dict["material"] = request.filters.material
                if request.filters.brand and request.filters.brand != "ALL":
                    filters_dict["brand"] = request.filters.brand
                if request.filters.customerState:
                    filters_dict["customerState"] = ", ".join(request.filters.customerState)
                if request.filters.industry:
                    filters_dict["industry"] = ", ".join(request.filters.industry)
                if request.filters.customerCategory and request.filters.customerCategory != "ALL":
                    filters_dict["customerCategory"] = request.filters.customerCategory
                if request.filters.customerType and request.filters.customerType != "ALL":
                    filters_dict["customerType"] = request.filters.customerType
                if request.filters.period:
                    filters_dict["period"] = request.filters.period
            
            if request.time:
                filters_dict["period"] = request.time.period
                filters_dict["fiscalYear"] = request.time.fiscalYear
        
        # Call chat service
        response = await chat_service.ask(
            question=request.question,
            filters=filters_dict,
            include_sql=request.includeSql,
            include_data=request.includeData,
        )
        
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Chat service error: {str(e)}"
        )


@router.get("/sales-analytics/chat/health")
async def chat_health_check():
    """Check health of the AI chat service."""
    from app.services.chat_service import get_chat_service
    
    try:
        chat_service = get_chat_service()
        health = await chat_service.health_check()
        
        return {
            "status": "healthy" if health["overall"] else "unhealthy",
            "components": health,
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/sales-analytics/chat/stats")
async def chat_stats():
    """Get AI chat service statistics."""
    from app.services.chat_service import get_chat_service
    
    try:
        chat_service = get_chat_service()
        return chat_service.get_stats()
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

