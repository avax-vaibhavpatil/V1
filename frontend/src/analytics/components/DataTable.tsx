/**
 * DataTable Component
 * 
 * Config-driven data table with:
 * - Sticky header and pinned columns
 * - Column groups with subcolumns
 * - Sorting, searching, pagination
 * - Conditional formatting
 */

import { useState, useMemo } from 'react';
import {
  Search,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import type { TableConfig, TableRow, FormatRules, ColumnConfig, ColumnGroupConfig } from '../types';
import { formatValue, getConditionalStyle } from '../utils/formatters';

// ============================================
// Types
// ============================================

interface DataTableProps {
  config: TableConfig;
  rows: TableRow[];
  total: number;
  page: number;
  pageSize: number;
  isLoading?: boolean;
  formatRules: FormatRules;
  highlightedGroup?: string;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
  searchTerm?: string;
  onSort: (key: string) => void;
  onSearch: (term: string) => void;
  onPageChange: (page: number) => void;
  onRowClick?: (row: TableRow) => void;
}

// ============================================
// Main Component
// ============================================

export default function DataTable({
  config,
  rows,
  total,
  page,
  pageSize,
  isLoading,
  formatRules,
  highlightedGroup,
  sortKey,
  sortDirection,
  searchTerm,
  onSort,
  onSearch,
  onPageChange,
  onRowClick,
}: DataTableProps) {
  const [localSearch, setLocalSearch] = useState(searchTerm || '');
  
  const totalPages = Math.ceil(total / pageSize);
  
  // Handle search with debounce-like behavior
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(localSearch);
  };
  
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSearch(e.target.value);
    // Also trigger search on clear
    if (e.target.value === '') {
      onSearch('');
    }
  };
  
  // Build flat column list for rendering
  const allColumns = useMemo(() => {
    const cols: (ColumnConfig & { groupKey?: string })[] = [];
    config.columnGroups.forEach(group => {
      group.columns.forEach(col => {
        cols.push({ ...col, groupKey: group.groupKey });
      });
    });
    return cols;
  }, [config.columnGroups]);
  
  return (
    <div className="bg-white border-t border-gray-200">
      {/* Table Header Actions */}
      <div className="px-6 py-4 flex items-center justify-between border-b border-gray-200">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={localSearch}
              onChange={handleSearchChange}
              placeholder={`Search ${config.entityColumn.label}...`}
              className="pl-9 pr-4 py-2 w-64 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            Search
          </button>
        </form>
        
        {/* Results Count */}
        <div className="text-sm text-gray-500">
          Showing {rows.length} of {total.toLocaleString()} results
        </div>
      </div>
      
      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          {/* Column Group Headers */}
          <thead>
            {/* Group Row */}
            <tr className="bg-gray-100">
              {/* Entity Column Group */}
              <th
                colSpan={config.entityColumn.secondaryKey ? 2 : 1}
                className="sticky left-0 z-10 bg-gray-100 px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200"
              >
                Entity
              </th>
              {/* Category Groups */}
              {config.columnGroups.map(group => (
                <th
                  key={group.groupKey}
                  colSpan={group.columns.length}
                  className={`px-4 py-2 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200 ${
                    highlightedGroup === group.groupKey ? 'bg-indigo-50 text-indigo-700' : ''
                  }`}
                >
                  {group.groupLabel}
                </th>
              ))}
            </tr>
            
            {/* Column Headers */}
            <tr className="bg-gray-50">
              {/* Entity Columns */}
              <th
                className="sticky left-0 z-10 bg-gray-50 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 border-r border-gray-200"
                onClick={() => onSort(config.entityColumn.key)}
              >
                <div className="flex items-center gap-1">
                  {config.entityColumn.label}
                  <SortIcon
                    active={sortKey === config.entityColumn.key}
                    direction={sortDirection}
                  />
                </div>
              </th>
              
              {config.entityColumn.secondaryKey && (
                <th className="sticky left-[200px] z-10 bg-gray-50 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                  {config.entityColumn.secondaryLabel || 'Code'}
                </th>
              )}
              
              {/* Data Columns */}
              {allColumns.map(col => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 ${
                    highlightedGroup === col.groupKey ? 'bg-indigo-50' : ''
                  }`}
                  onClick={() => col.sortable !== false && onSort(col.key)}
                  title={col.tooltip}
                >
                  <div className="flex items-center justify-end gap-1">
                    {col.label}
                    {col.sortable !== false && (
                      <SortIcon
                        active={sortKey === col.key}
                        direction={sortDirection}
                      />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          
          {/* Table Body */}
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              // Loading State
              Array.from({ length: 10 }).map((_, idx) => (
                <TableRowSkeleton
                  key={idx}
                  columnCount={allColumns.length + (config.entityColumn.secondaryKey ? 2 : 1)}
                />
              ))
            ) : rows.length === 0 ? (
              // Empty State
              <tr>
                <td
                  colSpan={allColumns.length + (config.entityColumn.secondaryKey ? 2 : 1)}
                  className="px-4 py-12 text-center text-gray-500"
                >
                  <div className="flex flex-col items-center">
                    <Search className="w-8 h-8 text-gray-300 mb-2" />
                    <p className="text-sm font-medium">No results found</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Try adjusting your search or filter criteria
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              // Data Rows
              rows.map((row, idx) => (
                <tr
                  key={row.entityId || idx}
                  onClick={() => onRowClick?.(row)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  {/* Entity Name */}
                  <td className="sticky left-0 z-10 bg-white px-4 py-3 text-sm font-medium text-gray-900 whitespace-nowrap border-r border-gray-100">
                    {row.entityName}
                  </td>
                  
                  {/* Regional Head / Secondary Column */}
                  {config.entityColumn.secondaryKey && (
                    <td className="sticky left-[200px] z-10 bg-white px-4 py-3 text-sm text-gray-500 whitespace-nowrap border-r border-gray-100">
                      {row.regionalHead || row[config.entityColumn.secondaryKey] || ''}
                    </td>
                  )}
                  
                  {/* Data Cells */}
                  {allColumns.map(col => {
                    const value = row[col.key];
                    const numValue = typeof value === 'number' ? value : parseFloat(value as string);
                    const style = col.conditional
                      ? getConditionalStyle(numValue, formatRules.conditionalStyles[col.conditional])
                      : null;
                    
                    return (
                      <td
                        key={col.key}
                        className={`px-4 py-3 text-sm text-right whitespace-nowrap text-gray-700 ${
                          highlightedGroup === col.groupKey ? 'bg-indigo-50' : ''
                        }`}
                        style={style ? { color: style.color } : undefined}
                      >
                        {formatValue(value, col.format)}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      {!isLoading && rows.length > 0 && (
        <div className="px-6 py-4 flex items-center justify-between border-t border-gray-200">
          <div className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            {/* Page Numbers */}
            {getPageNumbers(page, totalPages).map((pageNum, idx) => (
              pageNum === '...' ? (
                <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">...</span>
              ) : (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum as number)}
                  className={`px-3 py-1 text-sm rounded-lg ${
                    pageNum === page
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {pageNum}
                </button>
              )
            ))}
            
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// Helper Components
// ============================================

interface SortIconProps {
  active: boolean;
  direction?: 'asc' | 'desc';
}

function SortIcon({ active, direction }: SortIconProps) {
  if (!active) {
    return <ChevronsUpDown className="w-3.5 h-3.5 text-gray-400" />;
  }
  
  return direction === 'asc' ? (
    <ChevronUp className="w-3.5 h-3.5 text-indigo-600" />
  ) : (
    <ChevronDown className="w-3.5 h-3.5 text-indigo-600" />
  );
}

function TableRowSkeleton({ columnCount }: { columnCount: number }) {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: columnCount }).map((_, idx) => (
        <td key={idx} className="px-4 py-3">
          <div className="h-4 bg-gray-200 rounded w-full" />
        </td>
      ))}
    </tr>
  );
}

// ============================================
// Pagination Helper
// ============================================

function getPageNumbers(current: number, total: number): (number | string)[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  
  const pages: (number | string)[] = [];
  
  // Always show first page
  pages.push(1);
  
  if (current > 3) {
    pages.push('...');
  }
  
  // Show pages around current
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
    if (!pages.includes(i)) {
      pages.push(i);
    }
  }
  
  if (current < total - 2) {
    pages.push('...');
  }
  
  // Always show last page
  if (!pages.includes(total)) {
    pages.push(total);
  }
  
  return pages;
}

