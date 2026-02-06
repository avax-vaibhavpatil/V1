/**
 * API Adapter - Real Backend API Integration
 * 
 * This adapter connects to the FastAPI backend for real PostgreSQL data.
 * Replaces the mock data adapter for production use.
 */

import axios from 'axios';
import type {
  MetaResponse,
  KpisResponse,
  TableResponse,
  DrilldownResponse,
  FilterState,
  TimeState,
  ToggleState,
} from '../types';

// ============================================
// API Client Configuration
// ============================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================
// Request Types
// ============================================

export interface MetaRequest {
  reportId: string;
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
  entityViewMode?: string;
}

export interface DrilldownRequest {
  reportId: string;
  entityId: string;
  entityColumn?: string;
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
// API Functions
// ============================================

/**
 * GET /api/v1/reports/:reportId/meta
 * Returns metadata about the report
 */
export async function fetchMeta(request: MetaRequest): Promise<MetaResponse> {
  try {
    const response = await apiClient.get(`/api/v1/reports/${request.reportId}/meta`);
    return response.data;
  } catch (error) {
    console.error('Error fetching meta:', error);
    // Return default meta on error
    return {
      lastUpdatedAt: new Date().toISOString(),
      features: {
        export: true,
        drilldown: true,
        share: true,
        refresh: true,
      },
    };
  }
}

/**
 * POST /api/v1/reports/:reportId/kpis
 * Returns aggregated KPI data
 */
export async function fetchKpis(request: KpisRequest): Promise<KpisResponse> {
  try {
    const response = await apiClient.post(`/api/v1/reports/${request.reportId}/kpis`, {
      filters: request.filters,
      time: request.time,
      toggles: request.toggles,
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching KPIs:', error);
    return { cards: [] };
  }
}

/**
 * POST /api/v1/reports/:reportId/table
 * Returns paginated table data
 */
export async function fetchTable(request: TableRequest): Promise<TableResponse> {
  try {
    const response = await apiClient.post(`/api/v1/reports/${request.reportId}/table`, {
      filters: request.filters,
      time: request.time,
      toggles: request.toggles,
      pagination: request.pagination,
      sort: request.sort,
      search: request.search,
      entityViewMode: request.entityViewMode,
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching table:', error);
    return {
      rows: [],
      page: 1,
      pageSize: 50,
      total: 0,
    };
  }
}

/**
 * POST /api/v1/reports/:reportId/drilldown
 * Returns drilldown data for an entity
 */
export async function fetchDrilldown(request: DrilldownRequest): Promise<DrilldownResponse> {
  try {
    const response = await apiClient.post(`/api/v1/reports/${request.reportId}/drilldown`, {
      entityId: request.entityId,
      entityColumn: request.entityColumn,
      filters: request.filters,
      time: request.time,
      toggles: request.toggles,
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching drilldown:', error);
    throw error;
  }
}

/**
 * POST /api/v1/reports/:reportId/export
 * Export data as CSV
 */
export async function exportData(request: ExportRequest): Promise<string> {
  try {
    const response = await apiClient.post(`/api/v1/reports/${request.reportId}/export`, {
      filters: request.filters,
      time: request.time,
      toggles: request.toggles,
      format: request.format,
    });
    return response.data.csv;
  } catch (error) {
    console.error('Error exporting data:', error);
    throw error;
  }
}

// ============================================
// Export all functions
// ============================================

export const apiAdapter = {
  fetchMeta,
  fetchKpis,
  fetchTable,
  fetchDrilldown,
  exportData,
};

export default apiAdapter;



