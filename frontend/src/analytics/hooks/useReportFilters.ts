/**
 * useReportFilters Hook
 * 
 * Manages filter state with pending/applied pattern and URL synchronization.
 * Changes to filters don't trigger refetch until "Apply" is clicked.
 */

import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import type {
  ReportConfig,
  FilterState,
  TimeState,
  ToggleState,
  AppliedFilters,
} from '../types';

// ============================================
// Types
// ============================================

export interface UseReportFiltersReturn {
  // Pending state (not yet applied)
  pendingFilters: FilterState;
  pendingTime: TimeState;
  pendingToggles: ToggleState;
  
  // Applied state (triggers data fetching)
  appliedFilters: AppliedFilters;
  
  // State setters
  setPendingFilter: (key: string, value: string | string[] | undefined) => void;
  setPendingTime: (time: Partial<TimeState>) => void;
  setPendingToggle: (key: keyof ToggleState, value: string) => void;
  
  // Actions
  applyFilters: () => void;
  clearPending: () => void;
  resetToDefaults: () => void;
  
  // Computed
  hasChanges: boolean;
  appliedFilterCount: number;
}

// ============================================
// URL Serialization Helpers
// ============================================

function serializeFiltersToUrl(filters: AppliedFilters): Record<string, string> {
  const params: Record<string, string> = {};
  
  // Serialize filter state
  Object.entries(filters.filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        if (value.length > 0) {
          params[`f_${key}`] = value.join(',');
        }
      } else {
        params[`f_${key}`] = value;
      }
    }
  });
  
  // Serialize time state
  params.fy = filters.time.fiscalYear;
  params.period = filters.time.period;
  
  // Serialize toggles
  params.agg = filters.toggles.aggregation;
  params.mode = filters.toggles.metricMode;
  
  return params;
}

function deserializeFiltersFromUrl(
  searchParams: URLSearchParams,
  defaults: ReportConfig['defaults']
): AppliedFilters {
  const filters: FilterState = {};
  
  // Deserialize filter state
  searchParams.forEach((value, key) => {
    if (key.startsWith('f_')) {
      const filterKey = key.slice(2);
      if (value.includes(',')) {
        filters[filterKey] = value.split(',');
      } else {
        filters[filterKey] = value;
      }
    }
  });
  
  // Deserialize time state
  const time: TimeState = {
    fiscalYear: searchParams.get('fy') || defaults.time.fiscalYear,
    period: searchParams.get('period') || defaults.time.period,
  };
  
  // Deserialize toggles
  const toggles: ToggleState = {
    aggregation: (searchParams.get('agg') as ToggleState['aggregation']) || defaults.toggles.aggregation,
    metricMode: (searchParams.get('mode') as ToggleState['metricMode']) || defaults.toggles.metricMode,
  };
  
  return { filters, time, toggles };
}

// ============================================
// Hook Implementation
// ============================================

export function useReportFilters(config: ReportConfig): UseReportFiltersReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Initialize applied state from URL or defaults
  const initialApplied = useMemo(() => {
    return deserializeFiltersFromUrl(searchParams, config.defaults);
  }, []); // Only run once on mount
  
  // Applied state (what's currently in use)
  const [appliedFilters, setAppliedFilters] = useState<AppliedFilters>(initialApplied);
  
  // Pending state (user changes before applying)
  const [pendingFilters, setPendingFilters] = useState<FilterState>(initialApplied.filters);
  const [pendingTime, setPendingTimeState] = useState<TimeState>(initialApplied.time);
  const [pendingToggles, setPendingTogglesState] = useState<ToggleState>(initialApplied.toggles);
  
  // Refs to always have latest pending values (fixes stale closure issue)
  const pendingFiltersRef = useRef(pendingFilters);
  const pendingTimeRef = useRef(pendingTime);
  const pendingTogglesRef = useRef(pendingToggles);
  
  // Keep refs in sync with state
  useEffect(() => {
    pendingFiltersRef.current = pendingFilters;
  }, [pendingFilters]);
  
  useEffect(() => {
    pendingTimeRef.current = pendingTime;
  }, [pendingTime]);
  
  useEffect(() => {
    pendingTogglesRef.current = pendingToggles;
  }, [pendingToggles]);
  
  // Sync URL when applied filters change
  useEffect(() => {
    const newParams = serializeFiltersToUrl(appliedFilters);
    setSearchParams(newParams, { replace: true });
  }, [appliedFilters, setSearchParams]);
  
  // Set a single pending filter
  const setPendingFilter = useCallback((key: string, value: string | string[] | undefined) => {
    setPendingFilters(prev => {
      const next = { ...prev };
      if (value === undefined || (Array.isArray(value) && value.length === 0)) {
        delete next[key];
      } else {
        next[key] = value;
      }
      // Update ref immediately so applyFilters gets the new value
      pendingFiltersRef.current = next;
      return next;
    });
  }, []);
  
  // Set pending time
  const setPendingTime = useCallback((time: Partial<TimeState>) => {
    setPendingTimeState(prev => {
      const next = { ...prev, ...time };
      pendingTimeRef.current = next;
      return next;
    });
  }, []);
  
  // Set a pending toggle
  const setPendingToggle = useCallback((key: keyof ToggleState, value: string) => {
    setPendingTogglesState(prev => {
      const next = { ...prev, [key]: value };
      pendingTogglesRef.current = next;
      return next;
    });
  }, []);
  
  // Apply pending changes to become active
  // Uses refs to always get latest values (fixes stale closure when called after state update)
  const applyFilters = useCallback(() => {
    setAppliedFilters({
      filters: { ...pendingFiltersRef.current },
      time: { ...pendingTimeRef.current },
      toggles: { ...pendingTogglesRef.current },
    });
  }, []);
  
  // Clear pending changes (revert to applied)
  const clearPending = useCallback(() => {
    setPendingFilters(appliedFilters.filters);
    setPendingTimeState(appliedFilters.time);
    setPendingTogglesState(appliedFilters.toggles);
  }, [appliedFilters]);
  
  // Reset everything to config defaults
  const resetToDefaults = useCallback(() => {
    const defaultFilters: FilterState = {};
    
    // Set default segment values from config
    Object.entries(config.defaults.segments).forEach(([key, value]) => {
      defaultFilters[key] = value;
    });
    
    const defaults: AppliedFilters = {
      filters: defaultFilters,
      time: { ...config.defaults.time },
      toggles: { ...config.defaults.toggles },
    };
    
    setPendingFilters(defaults.filters);
    setPendingTimeState(defaults.time);
    setPendingTogglesState(defaults.toggles);
    setAppliedFilters(defaults);
  }, [config.defaults]);
  
  // Check if there are pending changes
  const hasChanges = useMemo(() => {
    const filtersChanged = JSON.stringify(pendingFilters) !== JSON.stringify(appliedFilters.filters);
    const timeChanged = JSON.stringify(pendingTime) !== JSON.stringify(appliedFilters.time);
    const togglesChanged = JSON.stringify(pendingToggles) !== JSON.stringify(appliedFilters.toggles);
    return filtersChanged || timeChanged || togglesChanged;
  }, [pendingFilters, pendingTime, pendingToggles, appliedFilters]);
  
  // Count applied filters
  const appliedFilterCount = useMemo(() => {
    let count = 0;
    Object.values(appliedFilters.filters).forEach(value => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          count += value.length;
        } else {
          count += 1;
        }
      }
    });
    return count;
  }, [appliedFilters.filters]);
  
  return {
    pendingFilters,
    pendingTime,
    pendingToggles,
    appliedFilters,
    setPendingFilter,
    setPendingTime,
    setPendingToggle,
    applyFilters,
    clearPending,
    resetToDefaults,
    hasChanges,
    appliedFilterCount,
  };
}

