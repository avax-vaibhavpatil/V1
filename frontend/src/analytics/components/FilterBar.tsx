/**
 * FilterBar Component
 * 
 * Global filter bar with time selectors, measure mode toggle,
 * and YTD/QTD/MTD selector. Opens advanced filter drawer.
 */

import { useState } from 'react';
import { SlidersHorizontal, X, Check, RotateCcw, ChevronDown } from 'lucide-react';
import type { ReportConfig, FilterState, TimeState, ToggleState } from '../types';
import { filterOptions } from '../data';

interface FilterBarProps {
  config: ReportConfig;
  pendingFilters: FilterState;
  pendingTime: TimeState;
  pendingToggles: ToggleState;
  appliedFilterCount: number;
  hasChanges: boolean;
  onFilterChange: (key: string, value: string | string[] | undefined) => void;
  onTimeChange: (time: Partial<TimeState>) => void;
  onToggleChange: (key: keyof ToggleState, value: string) => void;
  onApply: () => void;
  onClear: () => void;
  onReset: () => void;
}

export default function FilterBar({
  config,
  pendingFilters,
  pendingTime,
  pendingToggles,
  appliedFilterCount,
  hasChanges,
  onFilterChange,
  onTimeChange,
  onToggleChange,
  onApply,
  onClear,
  onReset,
}: FilterBarProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Get period options from config (if defined) or fall back to filterOptions
  const periodFilter = config.filters.find(f => f.key === 'period');
  const periodOptions = periodFilter?.options || filterOptions.periods;
  
  // Get fiscal year options from config (if defined) or fall back to filterOptions
  const fyFilter = config.filters.find(f => f.key === 'fiscalYear');
  const fiscalYearOptions = fyFilter?.options || filterOptions.fiscalYears;
  
  return (
    <div className="bg-white border-b border-gray-200">
      {/* Main Filter Row */}
      <div className="px-6 py-3 flex items-center gap-4 flex-wrap">
        {/* Fiscal Year Selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">FY:</label>
          <select
            value={pendingTime.fiscalYear}
            onChange={(e) => onTimeChange({ fiscalYear: e.target.value })}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            {fiscalYearOptions.map(fy => (
              <option key={fy.value} value={fy.value}>{fy.label}</option>
            ))}
          </select>
        </div>
        
        {/* Period Selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Period:</label>
          <select
            value={pendingTime.period}
            onChange={(e) => onTimeChange({ period: e.target.value })}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            {periodOptions.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
        
        {/* Aggregation Toggle (YTD/QTD/MTD) */}
        <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
          {filterOptions.aggregations.map(agg => (
            <button
              key={agg.value}
              onClick={() => onToggleChange('aggregation', agg.value)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                pendingToggles.aggregation === agg.value
                  ? 'bg-white text-indigo-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {agg.value}
            </button>
          ))}
        </div>
        
        {/* Metric Mode Toggle */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Mode:</label>
          <select
            value={pendingToggles.metricMode}
            onChange={(e) => onToggleChange('metricMode', e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            {filterOptions.metricModes.map(mode => (
              <option key={mode.value} value={mode.value}>{mode.label}</option>
            ))}
          </select>
        </div>
        
        {/* Spacer */}
        <div className="flex-1" />
        
        {/* Advanced Filters Button */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
            showAdvanced || appliedFilterCount > 0
              ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
              : 'text-gray-600 border-gray-300 hover:bg-gray-50'
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          <span>Filters</span>
          {appliedFilterCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-indigo-600 text-white rounded-full">
              {appliedFilterCount}
            </span>
          )}
          <ChevronDown className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
        </button>
        
        {/* Apply/Clear Buttons */}
        {hasChanges && (
          <div className="flex items-center gap-2">
            <button
              onClick={onClear}
              className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              Clear
            </button>
            <button
              onClick={onApply}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
            >
              <Check className="w-4 h-4" />
              Apply
            </button>
          </div>
        )}
      </div>
      
      {/* Advanced Filter Drawer */}
      {showAdvanced && (
        <AdvancedFilterDrawer
          config={config}
          pendingFilters={pendingFilters}
          onFilterChange={onFilterChange}
          onClose={() => setShowAdvanced(false)}
          onApply={() => {
            onApply();
            setShowAdvanced(false);
          }}
          onClear={onClear}
          onReset={onReset}
        />
      )}
    </div>
  );
}

// ============================================
// Advanced Filter Drawer
// ============================================

interface AdvancedFilterDrawerProps {
  config: ReportConfig;
  pendingFilters: FilterState;
  onFilterChange: (key: string, value: string | string[] | undefined) => void;
  onClose: () => void;
  onApply: () => void;
  onClear: () => void;
  onReset: () => void;
}

function AdvancedFilterDrawer({
  config,
  pendingFilters,
  onFilterChange,
  onClose,
  onApply,
  onClear,
  onReset,
}: AdvancedFilterDrawerProps) {
  return (
    <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Advanced Filters</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={onReset}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
          >
            <RotateCcw className="w-3 h-3" />
            Reset to Defaults
          </button>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Zone Filter */}
        <FilterSelect
          label="Zone"
          value={pendingFilters.zone}
          options={filterOptions.zones}
          onChange={(value) => onFilterChange('zone', value)}
          placeholder="All Zones"
        />
        
        {/* State Filter (dependent on zone) */}
        <FilterMultiSelect
          label="State"
          value={pendingFilters.state as string[] | undefined}
          options={getStateOptions(pendingFilters.zone as string | undefined)}
          onChange={(value) => onFilterChange('state', value)}
          placeholder="All States"
        />
        
        {/* Channel Type Filter */}
        <FilterSelect
          label="Channel Type"
          value={pendingFilters.channelType}
          options={filterOptions.channelTypes}
          onChange={(value) => onFilterChange('channelType', value)}
          placeholder="All Channels"
        />
        
        {/* Entity Type Filter */}
        <FilterSelect
          label="Entity Type"
          value={pendingFilters.entityType}
          options={filterOptions.entityTypes}
          onChange={(value) => onFilterChange('entityType', value)}
          placeholder="All Entities"
        />
        
        {/* Category Filter */}
        <FilterSelect
          label="Category"
          value={pendingFilters.category}
          options={filterOptions.categories}
          onChange={(value) => onFilterChange('category', value)}
          placeholder="All Categories"
        />
      </div>
      
      {/* Applied Filters Chips */}
      <AppliedFiltersChips
        pendingFilters={pendingFilters}
        onRemove={(key) => onFilterChange(key, undefined)}
      />
      
      {/* Action Buttons */}
      <div className="mt-4 flex items-center justify-end gap-3">
        <button
          onClick={onClear}
          className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          Clear All
        </button>
        <button
          onClick={onApply}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
        >
          Apply Filters
        </button>
      </div>
    </div>
  );
}

// ============================================
// Filter Input Components
// ============================================

interface FilterSelectProps {
  label: string;
  value: string | string[] | undefined;
  options: { value: string; label: string }[];
  onChange: (value: string | undefined) => void;
  placeholder?: string;
}

function FilterSelect({ label, value, options, onChange, placeholder }: FilterSelectProps) {
  const selectedValue = Array.isArray(value) ? value[0] : value;
  
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <select
        value={selectedValue || ''}
        onChange={(e) => onChange(e.target.value || undefined)}
        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
      >
        <option value="">{placeholder || 'Select...'}</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

interface FilterMultiSelectProps {
  label: string;
  value: string[] | undefined;
  options: { value: string; label: string }[];
  onChange: (value: string[] | undefined) => void;
  placeholder?: string;
}

function FilterMultiSelect({ label, value, options, onChange, placeholder }: FilterMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedValues = value || [];
  
  const toggleValue = (val: string) => {
    if (selectedValues.includes(val)) {
      const newValues = selectedValues.filter(v => v !== val);
      onChange(newValues.length > 0 ? newValues : undefined);
    } else {
      onChange([...selectedValues, val]);
    }
  };
  
  return (
    <div className="relative">
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-sm text-left border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
      >
        {selectedValues.length > 0
          ? `${selectedValues.length} selected`
          : placeholder || 'Select...'}
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 mt-3" />
      </button>
      
      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
            {options.map(opt => (
              <label
                key={opt.value}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedValues.includes(opt.value)}
                  onChange={() => toggleValue(opt.value)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ============================================
// Applied Filters Chips
// ============================================

interface AppliedFiltersChipsProps {
  pendingFilters: FilterState;
  onRemove: (key: string) => void;
}

function AppliedFiltersChips({ pendingFilters, onRemove }: AppliedFiltersChipsProps) {
  const chips: { key: string; label: string }[] = [];
  
  Object.entries(pendingFilters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        value.forEach(v => {
          chips.push({ key, label: `${key}: ${v}` });
        });
      } else {
        chips.push({ key, label: `${key}: ${value}` });
      }
    }
  });
  
  if (chips.length === 0) return null;
  
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {chips.map((chip, idx) => (
        <span
          key={`${chip.key}-${idx}`}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded-full"
        >
          {chip.label}
          <button
            onClick={() => onRemove(chip.key)}
            className="ml-1 hover:text-indigo-900"
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
    </div>
  );
}

// ============================================
// Helper: Get states based on zone
// ============================================

import { STATES_BY_ZONE, ALL_STATES } from '../data';

function getStateOptions(zone: string | undefined): { value: string; label: string }[] {
  if (zone && STATES_BY_ZONE[zone]) {
    return STATES_BY_ZONE[zone];
  }
  return ALL_STATES;
}

