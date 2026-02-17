"""
Reports API - Sales Analytics Endpoints

Provides API endpoints for the sales analytics dashboard.
Connects to PostgreSQL databases:
- analytics_llm: For Sales Analytics (sales_analytics table)
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
# Database Connection - analytics_llm
# ============================================

# Connection to the analytics_llm PostgreSQL database (uses .env config)
ANALYTICS_DB_URL = settings.database_url

analytics_engine = create_async_engine(
    ANALYTICS_DB_URL,
    pool_size=settings.ANALYTICS_DB_POOL_SIZE,
    max_overflow=settings.ANALYTICS_DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

AnalyticsSessionLocal = async_sessionmaker(
    analytics_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_analytics_db():
    """Get analytics database session (used for all reports)."""
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


# ============================================
# STOCK INVENTORY REPORT ENDPOINTS
# ============================================

class StockInventoryFilterState(BaseModel):
    stockView: Optional[str] = None
    stockCondition: Optional[str] = None
    agingBucket: Optional[str] = None
    branch: Optional[List[str]] = None
    company: Optional[List[str]] = None
    make: Optional[str] = None
    inventoryCategory: Optional[str] = None


class StockInventoryKpisRequest(BaseModel):
    filters: StockInventoryFilterState = StockInventoryFilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()


class StockInventoryTableRequest(BaseModel):
    filters: StockInventoryFilterState = StockInventoryFilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()
    pagination: PaginationParams = PaginationParams()
    sort: SortParams = SortParams()
    search: Optional[str] = None
    entityViewMode: str = "branch_name"


class StockInventoryDrilldownRequest(BaseModel):
    entityId: str
    entityColumn: str = "branch_name"
    filters: StockInventoryFilterState = StockInventoryFilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()


def build_stock_inventory_filter_clause(filters: StockInventoryFilterState, time: TimeState, aggregation: str = "MTD") -> tuple[str, dict]:
    """Build SQL WHERE clause from stock inventory filters."""
    clauses = []
    params = {}
    
    # Date filter - stock_gw uses stgw_date column
    # Parse period from time.period (e.g., "OCT", "October", "October 2025")
    if time.period:
        period_str = time.period.upper().strip()
        
        # Map month abbreviations and full names to month numbers
        month_map = {
            "JAN": 1, "JANUARY": 1,
            "FEB": 2, "FEBRUARY": 2,
            "MAR": 3, "MARCH": 3,
            "APR": 4, "APRIL": 4,
            "MAY": 5,
            "JUN": 6, "JUNE": 6,
            "JUL": 7, "JULY": 7,
            "AUG": 8, "AUGUST": 8,
            "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
            "OCT": 10, "OCTOBER": 10,
            "NOV": 11, "NOVEMBER": 11,
            "DEC": 12, "DECEMBER": 12,
        }
        
        # Extract month from period string
        month = None
        year = None
        
        # Try to find month in period string
        for key, value in month_map.items():
            if key in period_str:
                month = value
                break
        
        # Extract year from period string (look for 4-digit year)
        import re
        year_match = re.search(r'\b(20\d{2})\b', period_str)
        if year_match:
            year = int(year_match.group(1))
        else:
            # If no year found, determine from fiscal year
            # FY 2025-2026: April 2025 - March 2026
            if time.fiscalYear:
                fy_parts = time.fiscalYear.split('-')
                if len(fy_parts) == 2:
                    fy_start_year = int(fy_parts[0])
                    # April-December use first year, January-March use second year
                    if month and month >= 4:
                        year = fy_start_year
                    elif month and month <= 3:
                        year = fy_start_year + 1
        
        # Build date filter
        if month and year:
            if aggregation == "MTD":
                # Month to Date - filter by specific month/year
                clauses.append("EXTRACT(MONTH FROM stgw_date) = :filter_month")
                clauses.append("EXTRACT(YEAR FROM stgw_date) = :filter_year")
                params["filter_month"] = month
                params["filter_year"] = year
            elif aggregation == "QTD":
                # Quarter to Date - filter months from quarter start to selected month
                quarter_start_month = ((month - 1) // 3) * 3 + 1
                clauses.append("EXTRACT(YEAR FROM stgw_date) = :filter_year")
                clauses.append("EXTRACT(MONTH FROM stgw_date) >= :qtd_start_month")
                clauses.append("EXTRACT(MONTH FROM stgw_date) <= :qtd_end_month")
                params["filter_year"] = year
                params["qtd_start_month"] = quarter_start_month
                params["qtd_end_month"] = month
            elif aggregation == "YTD":
                # Year to Date - filter from fiscal year start (April) to selected month
                fy_start_year = year if month >= 4 else year - 1
                if month >= 4:
                    # April-December: same year
                    clauses.append("EXTRACT(YEAR FROM stgw_date) = :filter_year")
                    clauses.append("EXTRACT(MONTH FROM stgw_date) >= 4")
                    clauses.append("EXTRACT(MONTH FROM stgw_date) <= :ytd_end_month")
                    params["filter_year"] = fy_start_year
                    params["ytd_end_month"] = month
                else:
                    # January-March: previous year's April-December + current year's Jan-March
                    clauses.append(
                        "(EXTRACT(YEAR FROM stgw_date) = :fy_start_year AND EXTRACT(MONTH FROM stgw_date) >= 4) OR "
                        "(EXTRACT(YEAR FROM stgw_date) = :fy_end_year AND EXTRACT(MONTH FROM stgw_date) <= :ytd_end_month)"
                    )
                    params["fy_start_year"] = fy_start_year
                    params["fy_end_year"] = year
                    params["ytd_end_month"] = month
        else:
            # Fallback: just check date is not null
            clauses.append("stgw_date IS NOT NULL")
    else:
        # No period specified, get all data
        clauses.append("stgw_date IS NOT NULL")
    
    # Stock Condition filter
    if filters.stockCondition and filters.stockCondition != "ALL":
        condition_map = {
            "DRUM": "COALESCE(stgw_drum_val, 0) > 0",
            "GOOD": "COALESCE(stgw_good_val, 0) > 0",
            "CUT": "COALESCE(stgw_cut_val, 0) > 0",
            "SCRAP": "COALESCE(stgw_scrap_val, 0) > 0",
            "SMALL": "COALESCE(stgw_small_val, 0) > 0",
        }
        if filters.stockCondition in condition_map:
            clauses.append(condition_map[filters.stockCondition])
    
    # Aging Bucket filter
    if filters.agingBucket and filters.agingBucket != "ALL":
        aging_map = {
            "0_3M": "COALESCE(stgw_val0_3m, 0) > 0",
            "3_6M": "COALESCE(stgw_val3_6m, 0) > 0",
            "6M_1Y": "COALESCE(stgw_val6m_1y, 0) > 0",
            "1Y_2Y": "COALESCE(stgw_val1y_2y, 0) > 0",
            "2Y_3Y": "COALESCE(stgw_val2y_3y, 0) > 0",
            "3Y_4Y": "COALESCE(stgw_val3y_4y, 0) > 0",
            "ABV_4Y": "COALESCE(stgw_valabv_4y, 0) > 0",
        }
        if filters.agingBucket in aging_map:
            clauses.append(aging_map[filters.agingBucket])
    
    # Branch filter (multi-select)
    if filters.branch and len(filters.branch) > 0:
        placeholders = ", ".join([f":branch_{i}" for i in range(len(filters.branch))])
        clauses.append(f"branch_name IN ({placeholders})")
        for i, branch in enumerate(filters.branch):
            params[f"branch_{i}"] = branch
    
    # Company filter (multi-select)
    if filters.company and len(filters.company) > 0:
        placeholders = ", ".join([f":company_{i}" for i in range(len(filters.company))])
        clauses.append(f"company_name IN ({placeholders})")
        for i, company in enumerate(filters.company):
            params[f"company_{i}"] = company
    
    # Make filter
    if filters.make and filters.make != "ALL":
        clauses.append("stgw_make = :make")
        params["make"] = filters.make
    
    # Inventory Category filter
    if filters.inventoryCategory and filters.inventoryCategory != "ALL":
        # Assuming there's a column for inventory rating/category
        # Adjust column name based on your actual schema
        clauses.append("stgw_inventory_rating = :inventoryCategory")
        params["inventoryCategory"] = filters.inventoryCategory
    
    where_clause = " AND ".join(clauses) if clauses else "1=1"
    return where_clause, params


@router.get("/stock-inventory/meta")
async def get_stock_inventory_meta():
    """Get stock inventory report metadata."""
    async with AnalyticsSessionLocal() as session:
        try:
            # Get last updated from max date in data
            result = await session.execute(text(
                "SELECT MAX(stgw_date) as last_date FROM stock_gw"
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
                    "agingHeatmap": True,
                    "stockHealthScore": True,
                },
                "allowed": {
                    "branches": await get_distinct_stock_values(session, "branch_name"),
                    "companies": await get_distinct_stock_values(session, "company_name"),
                    "makes": await get_distinct_stock_values(session, "stgw_make"),
                }
            }
        except Exception as e:
            logger.error(f"Error fetching stock inventory meta: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def get_distinct_stock_values(session: AsyncSession, column: str) -> List[str]:
    """Get distinct non-null values from stock_gw table."""
    try:
        result = await session.execute(text(
            f"SELECT DISTINCT {column} FROM stock_gw WHERE {column} IS NOT NULL ORDER BY {column}"
        ))
        return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.warning(f"Error getting distinct values for {column}: {e}")
        return []


async def get_distinct_gateway_values(session: AsyncSession, column: str) -> List[str]:
    """Get distinct non-null values from gwanalytics table."""
    try:
        result = await session.execute(text(
            f"SELECT DISTINCT {column} FROM gwanalytics WHERE {column} IS NOT NULL ORDER BY {column}"
        ))
        return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.warning(f"Error getting distinct values for {column}: {e}")
        return []


@router.post("/stock-inventory/kpis")
async def get_stock_inventory_kpis(request: StockInventoryKpisRequest):
    """Get aggregated KPI data for stock inventory summary cards."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_stock_inventory_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            
            query = text(f"""
                SELECT 
                    -- Fresh Stock (0-3 Months)
                    COALESCE(SUM(stgw_val0_3m), 0) as stock0to3m,
                    COALESCE(SUM(stgw_qty0_3m), 0) as stock0to3mQty,
                    
                    -- Aging Stock components (3M-1Y) - calculate separately then combine
                    COALESCE(SUM(stgw_val3_6m), 0) as val3_6m,
                    COALESCE(SUM(stgw_val6m_1y), 0) as val6m_1y,
                    COALESCE(SUM(stgw_qty3_6m), 0) as qty3_6m,
                    COALESCE(SUM(stgw_qty6m_1y), 0) as qty6m_1y,
                    
                    -- Slow Moving (1-2 Years)
                    COALESCE(SUM(stgw_val1y_2y), 0) as stock1yto2y,
                    COALESCE(SUM(stgw_qty1y_2y), 0) as stock1yto2yQty,
                    
                    -- Dead Stock components (Above 2Y) - calculate separately
                    COALESCE(SUM(stgw_val2y_3y), 0) as val2y_3y,
                    COALESCE(SUM(stgw_val3y_4y), 0) as val3y_4y,
                    COALESCE(SUM(stgw_valabv_4y), 0) as valabv_4y,
                    COALESCE(SUM(stgw_qty2y_3y), 0) as qty2y_3y,
                    COALESCE(SUM(stgw_qty3y_4y), 0) as qty3y_4y,
                    COALESCE(SUM(stgw_qtyabv_4y), 0) as qtyabv_4y
                    
                FROM stock_gw
                WHERE {where_clause}
            """)
            
            result = await session.execute(query, params)
            row_tuple = result.fetchone()
            
            if not row_tuple:
                return {"cards": []}
            
            columns = result.keys()
            row = dict(zip(columns, row_tuple))
            
            # Extract values safely
            stock0to3m = float(row.get('stock0to3m', 0) or 0)
            stock0to3mQty = float(row.get('stock0to3mQty', 0) or 0)
            
            # Calculate 3M-1Y from components
            val3_6m = float(row.get('val3_6m', 0) or 0)
            val6m_1y = float(row.get('val6m_1y', 0) or 0)
            stock3mTo1y = val3_6m + val6m_1y
            qty3_6m = float(row.get('qty3_6m', 0) or 0)
            qty6m_1y = float(row.get('qty6m_1y', 0) or 0)
            stock3mTo1yQty = qty3_6m + qty6m_1y
            
            stock1yto2y = float(row.get('stock1yto2y', 0) or 0)
            stock1yto2yQty = float(row.get('stock1yto2yQty', 0) or 0)
            
            # Calculate Above 2Y from components
            val2y_3y = float(row.get('val2y_3y', 0) or 0)
            val3y_4y = float(row.get('val3y_4y', 0) or 0)
            valabv_4y = float(row.get('valabv_4y', 0) or 0)
            stockAbove2y = val2y_3y + val3y_4y + valabv_4y
            qty2y_3y = float(row.get('qty2y_3y', 0) or 0)
            qty3y_4y = float(row.get('qty3y_4y', 0) or 0)
            qtyabv_4y = float(row.get('qtyabv_4y', 0) or 0)
            stockAbove2yQty = qty2y_3y + qty3y_4y + qtyabv_4y
            
            # Calculate total from individual components (more reliable)
            total_stock_value = stock0to3m + stock3mTo1y + stock1yto2y + stockAbove2y
            total_stock_qty = stock0to3mQty + stock3mTo1yQty + stock1yto2yQty + stockAbove2yQty
            
            # Calculate percentages
            def calc_pct(value, total):
                return round((float(value) / total * 100) if total > 0 else 0, 1)
            
            cards = [
                {
                    "id": "freshStock",
                    "stock0to3m": stock0to3m,
                    "stock0to3mQty": stock0to3mQty,
                    "freshStockPct": calc_pct(stock0to3m, total_stock_value),
                },
                {
                    "id": "agingStock",
                    "stock3mTo1y": stock3mTo1y,
                    "stock3mTo1yQty": stock3mTo1yQty,
                    "agingStockPct": calc_pct(stock3mTo1y, total_stock_value),
                },
                {
                    "id": "slowMoving",
                    "stock1yto2y": stock1yto2y,
                    "stock1yto2yQty": stock1yto2yQty,
                    "slowMovingPct": calc_pct(stock1yto2y, total_stock_value),
                },
                {
                    "id": "deadStock",
                    "stockAbove2y": stockAbove2y,
                    "stockAbove2yQty": stockAbove2yQty,
                    "deadStockPct": calc_pct(stockAbove2y, total_stock_value),
                },
                {
                    "id": "totalStock",
                    "totalStockValue": total_stock_value,
                    "totalStockQty": total_stock_qty,
                },
            ]
            
            return {"cards": cards}
            
        except Exception as e:
            logger.error(f"Error fetching stock inventory KPIs: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock-inventory/table")
async def get_stock_inventory_table(request: StockInventoryTableRequest):
    """Get paginated table data for stock inventory with filtering, sorting, and search."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_stock_inventory_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            entity_column = request.entityViewMode or "branch_name"
            
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
                FROM stock_gw
                WHERE {where_clause} {search_clause}
                AND {entity_column} IS NOT NULL
            """)
            count_result = await session.execute(count_query, params)
            total = count_result.scalar() or 0
            
            # Calculate pagination
            offset = (request.pagination.page - 1) * request.pagination.pageSize
            params["limit"] = request.pagination.pageSize
            params["offset"] = offset
            
            # Main data query
            query = text(f"""
                SELECT 
                    {entity_column} as entity,
                    stgw_godown_code as entity_secondary,
                    
                    -- Aging 0-3 Months
                    SUM(COALESCE(stgw_val0_3m, 0)) as aging0to3m_value,
                    SUM(COALESCE(stgw_qty0_3m, 0)) as aging0to3m_qty,
                    
                    -- Aging 3-6 Months
                    SUM(COALESCE(stgw_val3_6m, 0)) as aging3to6m_value,
                    SUM(COALESCE(stgw_qty3_6m, 0)) as aging3to6m_qty,
                    
                    -- Aging 6M-1Y
                    SUM(COALESCE(stgw_val6m_1y, 0)) as aging6mTo1y_value,
                    SUM(COALESCE(stgw_qty6m_1y, 0)) as aging6mTo1y_qty,
                    
                    -- Aging 1-2 Years
                    SUM(COALESCE(stgw_val1y_2y, 0)) as aging1yTo2y_value,
                    SUM(COALESCE(stgw_qty1y_2y, 0)) as aging1yTo2y_qty,
                    
                    -- Aging Above 2 Years (Dead Stock)
                    SUM(COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + COALESCE(stgw_valabv_4y, 0)) as agingAbove2y_value,
                    SUM(COALESCE(stgw_qty2y_3y, 0) + COALESCE(stgw_qty3y_4y, 0) + COALESCE(stgw_qtyabv_4y, 0)) as agingAbove2y_qty,
                    
                    -- Good Stock
                    SUM(COALESCE(stgw_good_val, 0)) as good_value,
                    SUM(COALESCE(stgw_good_nos, 0)) as good_nos,
                    
                    -- Sales
                    SUM(COALESCE(stgw_sale_value, 0)) as sale_value,
                    SUM(COALESCE(stgw_sale90, 0)) as sale_90days,
                    SUM(COALESCE(stgw_profit_loss, 0)) as profit_loss,
                    
                    -- Total
                    SUM(COALESCE(stgw_val0_3m, 0) + COALESCE(stgw_val3_6m, 0) + COALESCE(stgw_val6m_1y, 0) + 
                        COALESCE(stgw_val1y_2y, 0) + COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + 
                        COALESCE(stgw_valabv_4y, 0)) as total_stock_value,
                    SUM(COALESCE(stgw_stock_lvl_value, 0)) as stock_level_value,
                    SUM(COALESCE(stgw_total_profit_loss, 0)) as total_profit_loss
                    
                FROM stock_gw
                WHERE {where_clause} {search_clause}
                AND {entity_column} IS NOT NULL
                GROUP BY {entity_column}, stgw_godown_code
                ORDER BY {sort_key} {sort_dir}
                LIMIT :limit OFFSET :offset
            """)
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            columns = result.keys()
            
            rows_formatted = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                # Calculate percentage for 0-3 months
                total_val = float(row_dict.get('total_stock_value', 0) or 0)
                aging0to3m_val = float(row_dict.get('aging0to3m_value', 0) or 0)
                row_dict['aging0to3m_pct'] = round((aging0to3m_val / total_val * 100) if total_val > 0 else 0, 1)
                
                # Format to match frontend expected structure
                formatted_row = {
                    "entityId": str(row_dict.get('entity', '')).replace(' ', '_').lower() if row_dict.get('entity') else '',
                    "entityName": row_dict.get('entity', ''),
                    "entityCode": str(row_dict.get('entity_secondary', '')),
                    **row_dict  # Include all other columns
                }
                rows_formatted.append(formatted_row)
            
            return {
                "rows": rows_formatted,
                "page": request.pagination.page,
                "pageSize": request.pagination.pageSize,
                "total": total,
            }
            
        except Exception as e:
            logger.error(f"Error fetching stock inventory table data: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock-inventory/drilldown")
async def get_stock_inventory_drilldown(request: StockInventoryDrilldownRequest):
    """Get detailed drilldown data for a specific stock inventory entity."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_stock_inventory_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            entity_column = request.entityColumn or "branch_name"
            
            # Add entity filter
            entity_clause = f"AND LOWER({entity_column}) = LOWER(:entity_id)"
            params["entity_id"] = request.entityId.replace("_", " ")
            
            # Get summary data
            summary_query = text(f"""
                SELECT 
                    COALESCE(SUM(stgw_val0_3m), 0) as total_fresh_stock,
                    COALESCE(SUM(stgw_val1y_2y), 0) as total_slow_moving,
                    COALESCE(SUM(stgw_val2y_3y), 0) + COALESCE(SUM(stgw_val3y_4y), 0) + 
                    COALESCE(SUM(stgw_valabv_4y), 0) as total_dead_stock,
                    COALESCE(SUM(stgw_sale_value), 0) as total_sales,
                    COALESCE(SUM(stgw_total_profit_loss), 0) as total_profit_loss
                FROM stock_gw
                WHERE {where_clause} {entity_clause}
            """)
            
            summary_result = await session.execute(summary_query, params)
            summary_row = summary_result.fetchone()
            
            if summary_row:
                columns = summary_result.keys()
                summary = dict(zip(columns, summary_row))
            else:
                summary = {}
            
            return {
                "summary": summary,
                "trend": [],  # Add trend data if needed
                "breakdown": {},  # Add breakdown data if needed
            }
            
        except Exception as e:
            logger.error(f"Error fetching stock inventory drilldown: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock-inventory/export")
async def export_stock_inventory(request: StockInventoryTableRequest):
    """Export stock inventory data to CSV."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_stock_inventory_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            entity_column = request.entityViewMode or "branch_name"
            
            # Get all data (no pagination for export)
            query = text(f"""
                SELECT 
                    {entity_column} as entity,
                    stgw_godown_code as entity_secondary,
                    SUM(COALESCE(stgw_val0_3m, 0)) as aging0to3m_value,
                    SUM(COALESCE(stgw_val3_6m, 0)) as aging3to6m_value,
                    SUM(COALESCE(stgw_val6m_1y, 0)) as aging6mTo1y_value,
                    SUM(COALESCE(stgw_val1y_2y, 0)) as aging1yTo2y_value,
                    SUM(COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + COALESCE(stgw_valabv_4y, 0)) as agingAbove2y_value,
                    SUM(COALESCE(stgw_val0_3m, 0) + COALESCE(stgw_val3_6m, 0) + COALESCE(stgw_val6m_1y, 0) + 
                        COALESCE(stgw_val1y_2y, 0) + COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + 
                        COALESCE(stgw_valabv_4y, 0)) as total_stock_value
                FROM stock_gw
                WHERE {where_clause}
                AND {entity_column} IS NOT NULL
                GROUP BY {entity_column}, stgw_godown_code
                ORDER BY total_stock_value DESC
            """)
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            columns = result.keys()
            
            # Build CSV
            csv_lines = [",".join(columns)]
            for row in rows:
                csv_lines.append(",".join([str(val) if val is not None else "" for val in row]))
            
            return {
                "csv": "\n".join(csv_lines),
                "filename": f"stock_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            }
            
        except Exception as e:
            logger.error(f"Error exporting stock inventory data: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ============================================
# GATEWAY ANALYTICS REPORT ENDPOINTS
# ============================================

class GatewayAnalyticsFilterState(BaseModel):
    company: Optional[List[str]] = None
    salesPerson: Optional[List[str]] = None
    industry: Optional[str] = None


class GatewayAnalyticsKpisRequest(BaseModel):
    filters: GatewayAnalyticsFilterState = GatewayAnalyticsFilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()


class GatewayAnalyticsTableRequest(BaseModel):
    filters: GatewayAnalyticsFilterState = GatewayAnalyticsFilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()
    pagination: PaginationParams = PaginationParams()
    sort: SortParams = SortParams()
    search: Optional[str] = None
    entityViewMode: str = "cust_name"


class GatewayAnalyticsDrilldownRequest(BaseModel):
    entityId: str
    entityColumn: str = "cust_name"
    filters: GatewayAnalyticsFilterState = GatewayAnalyticsFilterState()
    time: TimeState = TimeState()
    toggles: ToggleState = ToggleState()


def build_gateway_analytics_filter_clause(filters: GatewayAnalyticsFilterState, time: TimeState, aggregation: str = "YTD") -> tuple[str, dict]:
    """Build SQL WHERE clause from gateway analytics filters."""
    clauses = []
    params = {}
    
    # Date filter
    if time.period:
        clauses.append("gws_date IS NOT NULL")  # Placeholder - adjust based on actual date filtering needs
    
    # Company filter (multi-select)
    if filters.company and len(filters.company) > 0:
        placeholders = ", ".join([f":company_{i}" for i in range(len(filters.company))])
        clauses.append(f"company_name IN ({placeholders})")
        for i, company in enumerate(filters.company):
            params[f"company_{i}"] = company
    
    # Sales Person filter (multi-select)
    # Note: Adjust column name based on actual gwanalytics table schema
    if filters.salesPerson and len(filters.salesPerson) > 0:
        placeholders = ", ".join([f":salesperson_{i}" for i in range(len(filters.salesPerson))])
        # Use gws_salesperson or adjust based on actual column name
        clauses.append(f"gws_salesperson IN ({placeholders})")
        for i, sp in enumerate(filters.salesPerson):
            params[f"salesperson_{i}"] = sp
    
    # Industry filter
    # Note: Adjust column name based on actual gwanalytics table schema
    if filters.industry and filters.industry != "ALL":
        # Use gws_industry or adjust based on actual column name
        clauses.append("gws_industry = :industry")
        params["industry"] = filters.industry
    
    where_clause = " AND ".join(clauses) if clauses else "1=1"
    return where_clause, params


@router.get("/gateway-analytics/meta")
async def get_gateway_analytics_meta():
    """Get gateway analytics report metadata."""
    async with AnalyticsSessionLocal() as session:
        try:
            # Get last updated from max date in data
            result = await session.execute(text(
                "SELECT MAX(gws_date) as last_date FROM gwanalytics"
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
                    "companies": await get_distinct_gateway_values(session, "company_name"),
                    "salesPersons": await get_distinct_gateway_values(session, "gws_salesperson"),
                    "industries": await get_distinct_gateway_values(session, "gws_industry"),
                }
            }
        except Exception as e:
            logger.error(f"Error fetching gateway analytics meta: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway-analytics/kpis")
async def get_gateway_analytics_kpis(request: GatewayAnalyticsKpisRequest):
    """Get aggregated KPI data for gateway analytics summary cards."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_gateway_analytics_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            
            query = text(f"""
                SELECT 
                    COALESCE(SUM(gws_ytd_sales), 0) as ytdSales,
                    COALESCE(SUM(gws_os_amount), 0) as osAmount,
                    COALESCE(SUM(gws_os_abv_180), 0) as osAbv180,
                    COALESCE(SUM(gws_profit_loss), 0) as profitLoss,
                    COALESCE(SUM(gws_last90_sales), 0) as last90Sales
                FROM gwanalytics
                WHERE {where_clause}
            """)
            
            result = await session.execute(query, params)
            row_tuple = result.fetchone()
            
            if not row_tuple:
                return {"cards": []}
            
            columns = result.keys()
            row = dict(zip(columns, row_tuple))
            
            cards = [
                {
                    "id": "ytdSales",
                    "ytdSales": float(row.get('ytdSales', 0) or 0),
                },
                {
                    "id": "outstanding",
                    "osAmount": float(row.get('osAmount', 0) or 0),
                    "osAbv180": float(row.get('osAbv180', 0) or 0),
                },
                {
                    "id": "profitLoss",
                    "profitLoss": float(row.get('profitLoss', 0) or 0),
                },
                {
                    "id": "last90Sales",
                    "last90Sales": float(row.get('last90Sales', 0) or 0),
                },
            ]
            
            return {"cards": cards}
            
        except Exception as e:
            logger.error(f"Error fetching gateway analytics KPIs: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway-analytics/table")
async def get_gateway_analytics_table(request: GatewayAnalyticsTableRequest):
    """Get paginated table data for gateway analytics with filtering, sorting, and search."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_gateway_analytics_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            entity_column = request.entityViewMode or "cust_name"
            
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
                FROM gwanalytics
                WHERE {where_clause} {search_clause}
                AND {entity_column} IS NOT NULL
            """)
            count_result = await session.execute(count_query, params)
            total = count_result.scalar() or 0
            
            # Calculate pagination
            offset = (request.pagination.page - 1) * request.pagination.pageSize
            params["limit"] = request.pagination.pageSize
            params["offset"] = offset
            
            # Main data query
            query = text(f"""
                SELECT 
                    {entity_column} as entity,
                    gws_cust_code as entity_secondary,
                    
                    -- Sales
                    SUM(COALESCE(gws_ytd_sales, 0)) as ytd_sales,
                    SUM(COALESCE(gws_lytd_sales, 0)) as lytd_sales,
                    SUM(COALESCE(gws_last90_sales, 0)) as last90_sales,
                    SUM(COALESCE(gws_profit_loss, 0)) as profit_loss,
                    
                    -- Outstanding
                    SUM(COALESCE(gws_os_amount, 0)) as os_amount,
                    SUM(COALESCE(gws_os_abv_180, 0)) as os_abv_180,
                    SUM(COALESCE(gws_os_abv_90, 0)) as os_abv_90,
                    SUM(COALESCE(gws_due_os, 0)) as due_os,
                    
                    -- Pending
                    SUM(COALESCE(gws_pending_ao_amt, 0)) as pending_ao_amt,
                    SUM(COALESCE(gws_pending_quot_amt, 0)) as pending_quot_amt
                    
                FROM gwanalytics
                WHERE {where_clause} {search_clause}
                AND {entity_column} IS NOT NULL
                GROUP BY {entity_column}, gws_cust_code
                ORDER BY {sort_key} {sort_dir}
                LIMIT :limit OFFSET :offset
            """)
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            columns = result.keys()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            # Transform to match frontend expected format
            rows_formatted = []
            for row_dict in data:
                formatted_row = {
                    "entityId": str(row_dict.get('entity', '')).replace(' ', '_').lower() if row_dict.get('entity') else '',
                    "entityName": row_dict.get('entity', ''),
                    "entityCode": row_dict.get('entity_secondary', ''),
                    **row_dict  # Include all other columns
                }
                rows_formatted.append(formatted_row)
            
            return {
                "rows": rows_formatted,
                "page": request.pagination.page,
                "pageSize": request.pagination.pageSize,
                "total": total,
            }
            
        except Exception as e:
            logger.error(f"Error fetching gateway analytics table data: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway-analytics/drilldown")
async def get_gateway_analytics_drilldown(request: GatewayAnalyticsDrilldownRequest):
    """Get detailed drilldown data for a specific gateway analytics entity."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_gateway_analytics_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            entity_column = request.entityColumn or "cust_name"
            
            # Add entity filter
            entity_clause = f"AND LOWER({entity_column}) = LOWER(:entity_id)"
            params["entity_id"] = request.entityId.replace("_", " ")
            
            # Get summary data
            summary_query = text(f"""
                SELECT 
                    COALESCE(SUM(gws_ytd_sales), 0) as total_ytd_sales,
                    COALESCE(SUM(gws_os_amount), 0) as total_os,
                    COALESCE(SUM(gws_profit_loss), 0) as total_profit_loss,
                    COALESCE(SUM(gws_last90_sales), 0) as total_last90_sales
                FROM gwanalytics
                WHERE {where_clause} {entity_clause}
            """)
            
            summary_result = await session.execute(summary_query, params)
            summary_row = summary_result.fetchone()
            
            if summary_row:
                columns = summary_result.keys()
                summary = dict(zip(columns, summary_row))
            else:
                summary = {}
            
            return {
                "summary": summary,
                "trend": [],
                "breakdown": {},
            }
            
        except Exception as e:
            logger.error(f"Error fetching gateway analytics drilldown: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway-analytics/export")
async def export_gateway_analytics(request: GatewayAnalyticsTableRequest):
    """Export gateway analytics data to CSV."""
    async with AnalyticsSessionLocal() as session:
        try:
            where_clause, params = build_gateway_analytics_filter_clause(
                request.filters, request.time, request.toggles.aggregation
            )
            entity_column = request.entityViewMode or "cust_name"
            
            # Get all data (no pagination for export)
            query = text(f"""
                SELECT 
                    {entity_column} as entity,
                    gws_cust_code as entity_secondary,
                    SUM(COALESCE(gws_ytd_sales, 0)) as ytd_sales,
                    SUM(COALESCE(gws_os_amount, 0)) as os_amount,
                    SUM(COALESCE(gws_profit_loss, 0)) as profit_loss
                FROM gwanalytics
                WHERE {where_clause}
                AND {entity_column} IS NOT NULL
                GROUP BY {entity_column}, gws_cust_code
                ORDER BY ytd_sales DESC
            """)
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            columns = result.keys()
            
            # Build CSV
            csv_lines = [",".join(columns)]
            for row in rows:
                csv_lines.append(",".join([str(val) if val is not None else "" for val in row]))
            
            return {
                "csv": "\n".join(csv_lines),
                "filename": f"gateway_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            }
            
        except Exception as e:
            logger.error(f"Error exporting gateway analytics data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
