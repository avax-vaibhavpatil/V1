/**
 * ReportShell Component
 * 
 * Main container that orchestrates all dashboard components:
 * - ReportHeader
 * - FilterBar
 * - SegmentControls
 * - KpiGrid
 * - DataTable
 * - DrilldownDrawer
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  ReportConfig,
  MetaResponse,
  KpisResponse,
  TableResponse,
  DrilldownResponse,
  KpiClickAction,
  TableRow,
} from '../types';
import { useReportFilters } from '../hooks';
import {
  fetchMeta,
  fetchKpis,
  fetchTable,
  fetchDrilldown,
  exportData,
} from '../data';

import ReportHeader from './ReportHeader';
import FilterBar from './FilterBar';
import SegmentControls from './SegmentControls';
import { KpiGrid } from './KpiCard';
import DataTable from './DataTable';
import DrilldownDrawer from './DrilldownDrawer';
import ReportAIChat from './ReportAIChat';

// ============================================
// Types
// ============================================

interface ReportShellProps {
  config: ReportConfig;
}

// ============================================
// Main Component
// ============================================

export default function ReportShell({ config }: ReportShellProps) {
  // Filter state management
  const filterState = useReportFilters(config);
  
  // Data states
  const [meta, setMeta] = useState<MetaResponse | undefined>();
  const [kpis, setKpis] = useState<KpisResponse | undefined>();
  const [table, setTable] = useState<TableResponse | undefined>();
  
  // Loading states
  const [isLoadingMeta, setIsLoadingMeta] = useState(true);
  const [isLoadingKpis, setIsLoadingKpis] = useState(true);
  const [isLoadingTable, setIsLoadingTable] = useState(true);
  
  // Error states
  const [error, setError] = useState<string | undefined>();
  
  // Table state
  const [sortKey, setSortKey] = useState<string | undefined>(config.table.defaultSort?.key);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(config.table.defaultSort?.direction || 'desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  
  // UI state
  const [highlightedCategory, setHighlightedCategory] = useState<string | undefined>();
  const [drilldownEntity, setDrilldownEntity] = useState<{ id: string; name: string } | undefined>();
  const [drilldownData, setDrilldownData] = useState<DrilldownResponse | undefined>();
  const [isLoadingDrilldown, setIsLoadingDrilldown] = useState(false);
  const [drilldownError, setDrilldownError] = useState<string | undefined>();
  
  // Fetch meta data
  const loadMeta = useCallback(async () => {
    try {
      setIsLoadingMeta(true);
      const data = await fetchMeta({ reportId: config.reportId });
      setMeta(data);
    } catch (err) {
      setError('Failed to load report metadata');
    } finally {
      setIsLoadingMeta(false);
    }
  }, [config.reportId]);
  
  // Fetch KPIs
  const loadKpis = useCallback(async () => {
    try {
      setIsLoadingKpis(true);
      const data = await fetchKpis({
        reportId: config.reportId,
        filters: filterState.appliedFilters.filters,
        time: filterState.appliedFilters.time,
        toggles: filterState.appliedFilters.toggles,
      });
      setKpis(data);
    } catch (err) {
      console.error('Failed to load KPIs:', err);
    } finally {
      setIsLoadingKpis(false);
    }
  }, [config.reportId, filterState.appliedFilters]);
  
  // Fetch table data
  const loadTable = useCallback(async () => {
    try {
      setIsLoadingTable(true);
      const data = await fetchTable({
        reportId: config.reportId,
        filters: filterState.appliedFilters.filters,
        time: filterState.appliedFilters.time,
        toggles: filterState.appliedFilters.toggles,
        pagination: {
          page: currentPage,
          pageSize: config.table.pageSize || 50,
        },
        sort: sortKey ? { key: sortKey, direction: sortDirection } : undefined,
        search: searchTerm,
      });
      setTable(data);
    } catch (err) {
      console.error('Failed to load table:', err);
    } finally {
      setIsLoadingTable(false);
    }
  }, [
    config.reportId,
    config.table.pageSize,
    filterState.appliedFilters,
    currentPage,
    sortKey,
    sortDirection,
    searchTerm,
  ]);
  
  // Fetch drilldown data
  const loadDrilldown = useCallback(async (entityId: string) => {
    try {
      setIsLoadingDrilldown(true);
      setDrilldownError(undefined);
      const data = await fetchDrilldown({
        reportId: config.reportId,
        entityId,
        filters: filterState.appliedFilters.filters,
        time: filterState.appliedFilters.time,
        toggles: filterState.appliedFilters.toggles,
      });
      setDrilldownData(data);
    } catch (err) {
      setDrilldownError('Failed to load entity details');
    } finally {
      setIsLoadingDrilldown(false);
    }
  }, [config.reportId, filterState.appliedFilters]);
  
  // Initial load
  useEffect(() => {
    loadMeta();
  }, [loadMeta]);
  
  // Load data when filters change
  useEffect(() => {
    loadKpis();
    loadTable();
    setCurrentPage(1); // Reset to first page on filter change
  }, [filterState.appliedFilters]);
  
  // Load table when pagination/sort/search changes
  useEffect(() => {
    loadTable();
  }, [currentPage, sortKey, sortDirection, searchTerm]);
  
  // Load drilldown when entity is selected
  useEffect(() => {
    if (drilldownEntity) {
      loadDrilldown(drilldownEntity.id);
    }
  }, [drilldownEntity, loadDrilldown]);
  
  // Handlers
  const handleRefresh = () => {
    loadMeta();
    loadKpis();
    loadTable();
  };
  
  const handleExport = async (format: 'csv' | 'xlsx') => {
    try {
      const csvContent = await exportData({
        reportId: config.reportId,
        filters: filterState.appliedFilters.filters,
        time: filterState.appliedFilters.time,
        toggles: filterState.appliedFilters.toggles,
        format,
      });
      
      // Download file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${config.reportId}_export_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };
  
  const handleShare = () => {
    // Copy current URL to clipboard
    navigator.clipboard.writeText(window.location.href);
    // In production, show toast notification
  };
  
  const handleKpiClick = (action: KpiClickAction) => {
    if (action.type === 'filter' && action.filterKey && action.value) {
      filterState.setPendingFilter(action.filterKey, action.value);
      filterState.applyFilters();
    } else if (action.type === 'highlight' && action.groupKey) {
      setHighlightedCategory(prev => prev === action.groupKey ? undefined : action.groupKey);
    }
  };
  
  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('desc');
    }
    setCurrentPage(1);
  };
  
  const handleSearch = (term: string) => {
    setSearchTerm(term);
    setCurrentPage(1);
  };
  
  const handleRowClick = (row: TableRow) => {
    if (config.drilldown.enabled) {
      setDrilldownEntity({
        id: row.entityId as string,
        name: row.entityName as string,
      });
    }
  };
  
  const handleCloseDrilldown = () => {
    setDrilldownEntity(undefined);
    setDrilldownData(undefined);
  };
  
  // Get segment filters (tabs/chips)
  const segmentFilters = config.filters.filter(f => f.ui === 'tabs' || f.ui === 'chips');
  
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <ReportHeader
        config={config}
        meta={meta}
        isLoading={isLoadingMeta || isLoadingKpis || isLoadingTable}
        onRefresh={handleRefresh}
        onExport={handleExport}
        onShare={handleShare}
      />
      
      {/* Filter Bar */}
      <FilterBar
        config={config}
        pendingFilters={filterState.pendingFilters}
        pendingTime={filterState.pendingTime}
        pendingToggles={filterState.pendingToggles}
        appliedFilterCount={filterState.appliedFilterCount}
        hasChanges={filterState.hasChanges}
        onFilterChange={filterState.setPendingFilter}
        onTimeChange={filterState.setPendingTime}
        onToggleChange={filterState.setPendingToggle}
        onApply={filterState.applyFilters}
        onClear={filterState.clearPending}
        onReset={filterState.resetToDefaults}
      />
      
      {/* Segment Controls */}
      {segmentFilters.length > 0 && (
        <SegmentControls
          filters={segmentFilters}
          pendingFilters={filterState.pendingFilters}
          onFilterChange={(key, value) => {
            filterState.setPendingFilter(key, value);
            // Auto-apply segment changes
            setTimeout(() => filterState.applyFilters(), 0);
          }}
        />
      )}
      
      {/* KPI Grid */}
      <KpiGrid
        configs={config.kpis.cards}
        data={kpis?.cards || []}
        formatRules={config.formatRules}
        highlightedCategory={highlightedCategory}
        onCardClick={handleKpiClick}
        isLoading={isLoadingKpis}
      />
      
      {/* Data Table */}
      <div className="flex-1">
        <DataTable
          config={config.table}
          rows={table?.rows || []}
          total={table?.total || 0}
          page={currentPage}
          pageSize={config.table.pageSize || 50}
          isLoading={isLoadingTable}
          formatRules={config.formatRules}
          highlightedGroup={highlightedCategory}
          sortKey={sortKey}
          sortDirection={sortDirection}
          searchTerm={searchTerm}
          onSort={handleSort}
          onSearch={handleSearch}
          onPageChange={setCurrentPage}
          onRowClick={handleRowClick}
        />
      </div>
      
      {/* Drilldown Drawer */}
      {drilldownEntity && (
        <DrilldownDrawer
          config={config.drilldown}
          entityId={drilldownEntity.id}
          entityName={drilldownEntity.name}
          data={drilldownData}
          isLoading={isLoadingDrilldown}
          error={drilldownError}
          formatRules={config.formatRules}
          onClose={handleCloseDrilldown}
        />
      )}
      
      {/* AI Chat Assistant - uses reportId to call correct chat endpoint (sales vs stock) */}
      <ReportAIChat
        reportId={config.reportId}
        filters={filterState.appliedFilters.filters as Record<string, unknown>}
        time={filterState.appliedFilters.time}
        reportName={config.title}
        rows={table?.rows || []}
        kpis={kpis?.cards || []}
        aggregation={filterState.appliedFilters.toggles.aggregation}
      />
    </div>
  );
}

