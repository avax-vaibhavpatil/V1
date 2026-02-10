/**
 * Analytics Data Layer - Barrel Export
 * 
 * Smart data adapter that routes to either mock data or real API
 * based on the report configuration.
 */

import type {
  MetaResponse,
  KpisResponse,
  TableResponse,
  DrilldownResponse,
  FilterState,
  TimeState,
  ToggleState,
} from '../types';

// Mock data adapter (for primary-distributor-sales - demo)
import * as mockAdapter from './dataAdapter';

// Real API adapter (for sales-analytics - PostgreSQL)
import * as apiAdapter from './apiAdapter';

// ============================================
// Export mock data constants (for backward compatibility)
// ============================================

export {
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

interface MetaRequest {
  reportId: string;
  filters?: FilterState;
}

interface KpisRequest {
  reportId: string;
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
}

interface TableRequest {
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
  entityViewMode?: string;
}

interface DrilldownRequest {
  reportId: string;
  entityId: string;
  entityColumn?: string;
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
}

interface ExportRequest {
  reportId: string;
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
  format: 'csv' | 'xlsx';
}

// ============================================
// Reports that use real PostgreSQL API
// ============================================

const API_REPORTS = ['sales-analytics', 'stock-inventory', 'gateway-analytics'];

function usesRealApi(reportId: string): boolean {
  return API_REPORTS.includes(reportId);
}

// ============================================
// Smart Adapter Functions
// ============================================

/**
 * Fetch report metadata
 */
export async function fetchMeta(request: MetaRequest): Promise<MetaResponse> {
  if (usesRealApi(request.reportId)) {
    return apiAdapter.fetchMeta(request);
  }
  return mockAdapter.fetchMeta(request);
}

/**
 * Fetch KPI data
 */
export async function fetchKpis(request: KpisRequest): Promise<KpisResponse> {
  if (usesRealApi(request.reportId)) {
    return apiAdapter.fetchKpis(request);
  }
  return mockAdapter.fetchKpis(request);
}

/**
 * Fetch table data
 */
export async function fetchTable(request: TableRequest): Promise<TableResponse> {
  if (usesRealApi(request.reportId)) {
    return apiAdapter.fetchTable(request);
  }
  return mockAdapter.fetchTable(request);
}

/**
 * Fetch drilldown data
 */
export async function fetchDrilldown(request: DrilldownRequest): Promise<DrilldownResponse> {
  if (usesRealApi(request.reportId)) {
    return apiAdapter.fetchDrilldown(request);
  }
  return mockAdapter.fetchDrilldown(request);
}

/**
 * Export data
 */
export async function exportData(request: ExportRequest): Promise<string> {
  if (usesRealApi(request.reportId)) {
    return apiAdapter.exportData(request);
  }
  return mockAdapter.exportData(request);
}

/**
 * Fetch zones (mock only)
 */
export async function fetchZones() {
  return mockAdapter.fetchZones();
}

/**
 * Fetch states (mock only)
 */
export async function fetchStates(zone?: string) {
  return mockAdapter.fetchStates(zone);
}

// ============================================
// Filter Options (for mock adapter compatibility)
// ============================================

export { filterOptions } from './dataAdapter';
