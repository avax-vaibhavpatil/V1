/**
 * SegmentControls Component
 * 
 * Quick filters presented as tabs, chips, or button groups.
 * Supports single-select and multi-select modes.
 */

import type { FilterConfig, FilterState } from '../types';

interface SegmentControlsProps {
  filters: FilterConfig[];
  pendingFilters: FilterState;
  onFilterChange: (key: string, value: string | string[] | undefined) => void;
}

export default function SegmentControls({
  filters,
  pendingFilters,
  onFilterChange,
}: SegmentControlsProps) {
  // Only show segment controls for filters with tabs or chips UI
  const segmentFilters = filters.filter(f => f.ui === 'tabs' || f.ui === 'chips');
  
  if (segmentFilters.length === 0) return null;
  
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3">
      <div className="flex items-center gap-6 flex-wrap">
        {segmentFilters.map(filter => (
          <SegmentControl
            key={filter.key}
            filter={filter}
            value={pendingFilters[filter.key]}
            onChange={(value) => onFilterChange(filter.key, value)}
          />
        ))}
      </div>
    </div>
  );
}

// ============================================
// Single Segment Control
// ============================================

interface SegmentControlProps {
  filter: FilterConfig;
  value: string | string[] | undefined;
  onChange: (value: string | string[] | undefined) => void;
}

function SegmentControl({ filter, value, onChange }: SegmentControlProps) {
  const options = filter.options || [];
  const isMulti = filter.type === 'multi';
  const selectedValues = isMulti
    ? (Array.isArray(value) ? value : value ? [value] : [])
    : (Array.isArray(value) ? value[0] : value);
  
  if (filter.ui === 'tabs') {
    return (
      <TabsControl
        label={filter.label}
        options={options}
        value={selectedValues as string}
        onChange={onChange}
      />
    );
  }
  
  if (filter.ui === 'chips') {
    return (
      <ChipsControl
        label={filter.label}
        options={options}
        value={isMulti ? (selectedValues as string[]) : [selectedValues as string].filter(Boolean)}
        isMulti={isMulti}
        onChange={(vals) => {
          if (isMulti) {
            onChange(vals.length > 0 ? vals : undefined);
          } else {
            onChange(vals[0] || undefined);
          }
        }}
      />
    );
  }
  
  return null;
}

// ============================================
// Tabs Control
// ============================================

interface TabsControlProps {
  label: string;
  options: { value: string; label: string }[];
  value: string | undefined;
  onChange: (value: string | undefined) => void;
}

function TabsControl({ label, options, value, onChange }: TabsControlProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm font-medium text-gray-600">{label}:</span>
      <div className="flex bg-gray-100 rounded-lg p-0.5">
        {options.map(opt => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value === value ? undefined : opt.value)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
              opt.value === value
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ============================================
// Chips Control
// ============================================

interface ChipsControlProps {
  label: string;
  options: { value: string; label: string }[];
  value: string[];
  isMulti: boolean;
  onChange: (values: string[]) => void;
}

function ChipsControl({ label, options, value, isMulti, onChange }: ChipsControlProps) {
  const toggleValue = (val: string) => {
    if (isMulti) {
      if (value.includes(val)) {
        onChange(value.filter(v => v !== val));
      } else {
        onChange([...value, val]);
      }
    } else {
      // Single select - toggle or select new
      onChange(value.includes(val) ? [] : [val]);
    }
  };
  
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm font-medium text-gray-600">{label}:</span>
      <div className="flex flex-wrap gap-2">
        {options.map(opt => {
          const isSelected = value.includes(opt.value);
          return (
            <button
              key={opt.value}
              onClick={() => toggleValue(opt.value)}
              className={`px-3 py-1.5 text-sm font-medium rounded-full border transition-all ${
                isSelected
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-300 hover:text-indigo-600'
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

