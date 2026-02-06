/**
 * Data Adapter - Simulates Backend API Endpoints
 * 
 * This adapter provides mock implementations of the API contract.
 * It can be easily swapped with real API calls by replacing the implementations.
 */

import type {
  MetaResponse,
  KpisResponse,
  TableResponse,
  DrilldownResponse,
  FilterState,
  TimeState,
  ToggleState,
  TableRow,
} from '../types';

import {
  getMockData,
  aggregateKpis,
  generateTrendData,
  generateBreakdownData,
  ZONES,
  STATES_BY_ZONE,
  ALL_STATES,
  CATEGORIES,
  FISCAL_YEARS,
  PERIODS,
  CHANNEL_TYPES,
  ENTITY_TYPES,
  AGGREGATIONS,
  METRIC_MODES,
} from './mockDataGenerator';

// ============================================
// Request Types
// ============================================

export interface MetaRequest {
  reportId: string;
  filters?: FilterState;
}

export interface KpisRequest {
  reportId: string;
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
}

export interface TableRequest {
  reportId: string;
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
  pagination: {
    page: number;
    pageSize: number;
  };
  sort?: {
    key: string;
    direction: 'asc' | 'desc';
  };
  search?: string;
}

export interface DrilldownRequest {
  reportId: string;
  entityId: string;
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
}

export interface ExportRequest {
  reportId: string;
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
  format: 'csv' | 'xlsx';
}

// ============================================
// Helper Functions
// ============================================

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function filterRows(rows: TableRow[], filters: FilterState): TableRow[] {
  return rows.filter(row => {
    // Filter by zone
    if (filters.zone) {
      const zones = Array.isArray(filters.zone) ? filters.zone : [filters.zone];
      if (zones.length > 0 && !zones.includes(row.zone as string)) {
        return false;
      }
    }
    
    // Filter by state
    if (filters.state) {
      const states = Array.isArray(filters.state) ? filters.state : [filters.state];
      if (states.length > 0 && !states.includes(row.state as string)) {
        return false;
      }
    }
    
    // Filter by channel type
    if (filters.channelType) {
      if (row.channelType !== filters.channelType) {
        return false;
      }
    }
    
    // Filter by entity type
    if (filters.entityType) {
      if (row.entityType !== filters.entityType) {
        return false;
      }
    }
    
    // Filter by category (for KPI click filtering)
    if (filters.category) {
      const categoryKey = filters.category as string;
      const actualSalesKey = `${categoryKey}_actualSales`;
      const actualSales = row[actualSalesKey] as number;
      if (!actualSales || actualSales <= 0) {
        return false;
      }
    }
    
    return true;
  });
}

function searchRows(rows: TableRow[], searchTerm: string): TableRow[] {
  if (!searchTerm || searchTerm.trim() === '') {
    return rows;
  }
  
  const term = searchTerm.toLowerCase().trim();
  return rows.filter(row => {
    const name = (row.entityName as string || '').toLowerCase();
    const code = (row.entityCode as string || '').toLowerCase();
    return name.includes(term) || code.includes(term);
  });
}

function sortRows(rows: TableRow[], sortKey: string, direction: 'asc' | 'desc'): TableRow[] {
  return [...rows].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    
    // Handle nulls/undefined
    if (aVal === undefined || aVal === null) return direction === 'asc' ? 1 : -1;
    if (bVal === undefined || bVal === null) return direction === 'asc' ? -1 : 1;
    
    // Numeric comparison
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return direction === 'asc' ? aVal - bVal : bVal - aVal;
    }
    
    // String comparison
    const aStr = String(aVal).toLowerCase();
    const bStr = String(bVal).toLowerCase();
    const comparison = aStr.localeCompare(bStr);
    return direction === 'asc' ? comparison : -comparison;
  });
}

function paginateRows(rows: TableRow[], page: number, pageSize: number): TableRow[] {
  const startIndex = (page - 1) * pageSize;
  return rows.slice(startIndex, startIndex + pageSize);
}

function applyAggregation(rows: TableRow[], aggregation: string, period: string): TableRow[] {
  // In a real implementation, this would filter data based on the time aggregation
  // For mock data, we just return the rows with a scaling factor
  const scaleFactor = aggregation === 'YTD' ? 1 : aggregation === 'QTD' ? 0.25 : 0.0833;
  
  return rows.map(row => {
    const scaledRow = { ...row };
    
    // Scale numeric values based on aggregation
    CATEGORIES.forEach(cat => {
      const actualKey = `${cat.key}_actualSales`;
      const targetKey = `${cat.key}_targetSales`;
      
      if (typeof scaledRow[actualKey] === 'number') {
        scaledRow[actualKey] = Number(((scaledRow[actualKey] as number) * scaleFactor).toFixed(2));
      }
      if (typeof scaledRow[targetKey] === 'number') {
        scaledRow[targetKey] = Number(((scaledRow[targetKey] as number) * scaleFactor).toFixed(2));
      }
    });
    
    // Recalculate overall metrics
    let totalActual = 0;
    let totalTarget = 0;
    CATEGORIES.forEach(cat => {
      totalActual += (scaledRow[`${cat.key}_actualSales`] as number) || 0;
      totalTarget += (scaledRow[`${cat.key}_targetSales`] as number) || 0;
    });
    
    scaledRow.overall_actualSales = Number(totalActual.toFixed(2));
    scaledRow.overall_targetSales = Number(totalTarget.toFixed(2));
    
    return scaledRow;
  });
}

// ============================================
// API Simulation Functions
// ============================================

/**
 * GET /api/reports/:reportId/meta
 * Returns metadata about the report including last updated time and allowed filter values
 */
export async function fetchMeta(request: MetaRequest): Promise<MetaResponse> {
  await delay(200); // Simulate network latency
  
  return {
    lastUpdatedAt: new Date().toISOString(),
    features: {
      export: true,
      drilldown: true,
      share: true,
      refresh: true,
    },
    allowed: {
      zone: ZONES.map(z => z.value),
      state: ALL_STATES.map(s => s.value),
      channelType: CHANNEL_TYPES.map(c => c.value),
      entityType: ENTITY_TYPES.map(e => e.value),
    },
  };
}

/**
 * POST /api/reports/:reportId/kpis
 * Returns aggregated KPI data for the summary cards
 */
export async function fetchKpis(request: KpisRequest): Promise<KpisResponse> {
  await delay(300); // Simulate network latency
  
  const mockData = getMockData();
  let filteredRows = filterRows(mockData.rows, request.filters);
  filteredRows = applyAggregation(filteredRows, request.toggles.aggregation, request.time.period);
  
  const kpiAggregates = aggregateKpis(filteredRows);
  
  return {
    cards: kpiAggregates.map(kpi => ({
      id: kpi.id,
      actualSales: kpi.actualSales,
      targetSales: kpi.targetSales,
      growthPct: kpi.growthPct,
      contributionPct: kpi.contributionPct,
      previousPeriodSales: kpi.previousPeriodSales || 0,
    })),
  };
}

/**
 * POST /api/reports/:reportId/table
 * Returns paginated table data with filtering, sorting, and search
 */
export async function fetchTable(request: TableRequest): Promise<TableResponse> {
  await delay(400); // Simulate network latency
  
  const mockData = getMockData();
  
  // Apply filters
  let processedRows = filterRows(mockData.rows, request.filters);
  
  // Apply aggregation
  processedRows = applyAggregation(processedRows, request.toggles.aggregation, request.time.period);
  
  // Apply search
  if (request.search) {
    processedRows = searchRows(processedRows, request.search);
  }
  
  // Get total before pagination
  const total = processedRows.length;
  
  // Apply sorting
  if (request.sort) {
    processedRows = sortRows(processedRows, request.sort.key, request.sort.direction);
  } else {
    // Default sort by overall actual sales descending
    processedRows = sortRows(processedRows, 'overall_actualSales', 'desc');
  }
  
  // Apply pagination
  const paginatedRows = paginateRows(processedRows, request.pagination.page, request.pagination.pageSize);
  
  return {
    rows: paginatedRows,
    page: request.pagination.page,
    pageSize: request.pagination.pageSize,
    total,
  };
}

/**
 * POST /api/reports/:reportId/drilldown
 * Returns detailed data for a specific entity
 */
export async function fetchDrilldown(request: DrilldownRequest): Promise<DrilldownResponse> {
  await delay(350); // Simulate network latency
  
  const mockData = getMockData();
  const entity = mockData.rows.find(row => row.entityId === request.entityId);
  
  if (!entity) {
    throw new Error(`Entity not found: ${request.entityId}`);
  }
  
  // Generate summary metrics from entity data
  const summary: Record<string, number> = {};
  CATEGORIES.forEach(cat => {
    summary[`${cat.key}_actualSales`] = (entity[`${cat.key}_actualSales`] as number) || 0;
    summary[`${cat.key}_targetSales`] = (entity[`${cat.key}_targetSales`] as number) || 0;
    summary[`${cat.key}_growthPct`] = (entity[`${cat.key}_growthPct`] as number) || 0;
  });
  summary.overall_actualSales = (entity.overall_actualSales as number) || 0;
  summary.overall_targetSales = (entity.overall_targetSales as number) || 0;
  summary.overall_growthPct = (entity.overall_growthPct as number) || 0;
  
  // Generate trend data
  const trend = generateTrendData(request.entityId);
  
  // Generate breakdown data
  const breakdown = generateBreakdownData(request.entityId);
  
  return {
    entity: {
      id: entity.entityId as string,
      name: entity.entityName as string,
      code: entity.entityCode as string,
    },
    summary,
    trend,
    breakdown,
  };
}

/**
 * GET /api/dimensions/zones
 * Returns available zones
 */
export async function fetchZones(): Promise<{ value: string; label: string }[]> {
  await delay(100);
  return ZONES;
}

/**
 * GET /api/dimensions/states
 * Returns available states, optionally filtered by zone
 */
export async function fetchStates(zone?: string): Promise<{ value: string; label: string }[]> {
  await delay(100);
  
  if (zone && STATES_BY_ZONE[zone]) {
    return STATES_BY_ZONE[zone];
  }
  
  return ALL_STATES;
}

/**
 * Export data to CSV
 */
export async function exportData(request: ExportRequest): Promise<string> {
  await delay(500);
  
  const mockData = getMockData();
  let filteredRows = filterRows(mockData.rows, request.filters);
  filteredRows = applyAggregation(filteredRows, request.toggles.aggregation, request.time.period);
  
  // Generate CSV content
  const headers = [
    'Entity ID',
    'Entity Name',
    'Entity Type',
    'Channel Type',
    'Zone',
    'State',
    ...CATEGORIES.flatMap(cat => [
      `${cat.label} Actual`,
      `${cat.label} Target`,
      `${cat.label} Growth %`,
    ]),
    'Overall Actual',
    'Overall Target',
    'Overall Growth %',
  ];
  
  const csvRows = [headers.join(',')];
  
  filteredRows.forEach(row => {
    const values = [
      row.entityId,
      `"${row.entityName}"`,
      row.entityType,
      row.channelType,
      row.zone,
      row.state,
      ...CATEGORIES.flatMap(cat => [
        row[`${cat.key}_actualSales`],
        row[`${cat.key}_targetSales`],
        row[`${cat.key}_growthPct`],
      ]),
      row.overall_actualSales,
      row.overall_targetSales,
      row.overall_growthPct,
    ];
    csvRows.push(values.join(','));
  });
  
  return csvRows.join('\n');
}

// ============================================
// Static Filter Options
// ============================================

export const filterOptions = {
  fiscalYears: FISCAL_YEARS,
  periods: PERIODS,
  channelTypes: CHANNEL_TYPES,
  entityTypes: ENTITY_TYPES,
  aggregations: AGGREGATIONS,
  metricModes: METRIC_MODES,
  zones: ZONES,
  categories: CATEGORIES.map(c => ({ value: c.key, label: c.label })),
};

