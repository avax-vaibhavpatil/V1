/**
 * DrilldownDrawer Component
 * 
 * Right-side drawer showing detailed data for a selected entity:
 * - Entity summary KPIs
 * - Trend chart (time series)
 * - Breakdown by category/product
 */

import { useEffect, useState } from 'react';
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
  PieChart,
  LineChart,
  Loader2,
} from 'lucide-react';
import type {
  DrilldownConfig,
  DrilldownResponse,
  DrilldownWidget,
  FormatRules,
} from '../types';
import { formatCurrency, formatPercent, getConditionalStyle } from '../utils/formatters';
import { CATEGORIES } from '../data';

// ============================================
// Types
// ============================================

interface DrilldownDrawerProps {
  config: DrilldownConfig;
  entityId: string;
  entityName: string;
  data?: DrilldownResponse;
  isLoading?: boolean;
  error?: string;
  formatRules: FormatRules;
  onClose: () => void;
}

// ============================================
// Main Component
// ============================================

export default function DrilldownDrawer({
  config,
  entityId,
  entityName,
  data,
  isLoading,
  error,
  formatRules,
  onClose,
}: DrilldownDrawerProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-2xl z-50 flex flex-col animate-slide-in-right">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{entityName}</h2>
            <p className="text-sm text-gray-500">Entity ID: {entityId}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <LoadingState />
          ) : error ? (
            <ErrorState message={error} />
          ) : data ? (
            <div className="space-y-6">
              {config.widgets.map(widget => (
                <WidgetRenderer
                  key={widget}
                  widget={widget}
                  data={data}
                  formatRules={formatRules}
                />
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}

// ============================================
// Widget Renderer
// ============================================

interface WidgetRendererProps {
  widget: DrilldownWidget;
  data: DrilldownResponse;
  formatRules: FormatRules;
}

function WidgetRenderer({ widget, data, formatRules }: WidgetRendererProps) {
  switch (widget) {
    case 'entitySummary':
      return <EntitySummaryWidget data={data} formatRules={formatRules} />;
    case 'trendChart':
      return <TrendChartWidget data={data} />;
    case 'breakdownByCategory':
      return <BreakdownWidget title="Category Breakdown" data={data.breakdown.byCategory} formatRules={formatRules} />;
    case 'breakdownByProduct':
      return <BreakdownWidget title="Top Products" data={data.breakdown.byProduct} formatRules={formatRules} />;
    default:
      return null;
  }
}

// ============================================
// Entity Summary Widget
// ============================================

function EntitySummaryWidget({
  data,
  formatRules,
}: {
  data: DrilldownResponse;
  formatRules: FormatRules;
}) {
  const overallActual = data.summary.overall_actualSales || 0;
  const overallTarget = data.summary.overall_targetSales || 0;
  const overallGrowth = data.summary.overall_growthPct || 0;
  
  const growthStyle = getConditionalStyle(overallGrowth, formatRules.conditionalStyles.posNeg);
  
  return (
    <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
      <h3 className="text-sm font-medium opacity-80 mb-4">Overall Performance</h3>
      
      <div className="grid grid-cols-3 gap-4">
        {/* Actual Sales */}
        <div>
          <div className="text-3xl font-bold">{formatCurrency(overallActual)}</div>
          <div className="text-sm opacity-80">Actual Sales</div>
        </div>
        
        {/* Target Sales */}
        <div>
          <div className="text-2xl font-semibold">{formatCurrency(overallTarget)}</div>
          <div className="text-sm opacity-80">Target</div>
        </div>
        
        {/* Growth */}
        <div>
          <div className="flex items-center gap-2">
            {growthStyle.icon === 'arrowUp' && <TrendingUp className="w-6 h-6" />}
            {growthStyle.icon === 'arrowDown' && <TrendingDown className="w-6 h-6" />}
            {growthStyle.icon === 'dash' && <Minus className="w-6 h-6" />}
            <span className="text-2xl font-semibold">{formatPercent(overallGrowth, true)}</span>
          </div>
          <div className="text-sm opacity-80">Growth</div>
        </div>
      </div>
      
      {/* Category Breakdown Mini */}
      <div className="mt-6 pt-4 border-t border-white/20">
        <div className="grid grid-cols-3 gap-3">
          {CATEGORIES.slice(0, 6).map(cat => {
            const actual = data.summary[`${cat.key}_actualSales`] || 0;
            return (
              <div key={cat.key} className="text-center">
                <div className="text-lg font-semibold">{formatCurrency(actual)}</div>
                <div className="text-xs opacity-70">{cat.shortLabel}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ============================================
// Trend Chart Widget (Simple Bar Chart)
// ============================================

function TrendChartWidget({ data }: { data: DrilldownResponse }) {
  const maxValue = Math.max(...data.trend.map(t => Math.max(t.value, t.target || 0)));
  
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <LineChart className="w-5 h-5 text-indigo-600" />
        <h3 className="text-lg font-semibold text-gray-900">Monthly Trend</h3>
      </div>
      
      <div className="flex items-end gap-2 h-48">
        {data.trend.map((point, idx) => {
          const height = maxValue > 0 ? (point.value / maxValue) * 100 : 0;
          const targetHeight = maxValue > 0 && point.target ? (point.target / maxValue) * 100 : 0;
          
          return (
            <div key={idx} className="flex-1 flex flex-col items-center gap-1">
              <div className="relative w-full flex justify-center gap-0.5" style={{ height: '160px' }}>
                {/* Target Bar */}
                {point.target && (
                  <div
                    className="w-2 bg-gray-200 rounded-t self-end"
                    style={{ height: `${targetHeight}%` }}
                    title={`Target: ${formatCurrency(point.target)}`}
                  />
                )}
                {/* Actual Bar */}
                <div
                  className="w-3 bg-indigo-500 rounded-t self-end transition-all hover:bg-indigo-600"
                  style={{ height: `${height}%` }}
                  title={`Actual: ${formatCurrency(point.value)}`}
                />
              </div>
              <span className="text-xs text-gray-500">{point.period}</span>
            </div>
          );
        })}
      </div>
      
      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-indigo-500 rounded" />
          <span className="text-xs text-gray-600">Actual</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-gray-200 rounded" />
          <span className="text-xs text-gray-600">Target</span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Breakdown Widget
// ============================================

function BreakdownWidget({
  title,
  data,
  formatRules,
}: {
  title: string;
  data?: { name: string; value: number; percentage: number; growth?: number }[];
  formatRules: FormatRules;
}) {
  if (!data || data.length === 0) return null;
  
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-indigo-600" />
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      
      <div className="space-y-3">
        {data.map((item, idx) => {
          const barWidth = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
          const growthStyle = item.growth !== undefined
            ? getConditionalStyle(item.growth, formatRules.conditionalStyles.posNeg)
            : null;
          
          return (
            <div key={idx}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">{item.name}</span>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-600">{formatCurrency(item.value)}</span>
                  <span className="text-xs text-gray-400">{formatPercent(item.percentage)}</span>
                  {item.growth !== undefined && growthStyle && (
                    <span
                      className="text-xs font-medium"
                      style={{ color: growthStyle.color }}
                    >
                      {formatPercent(item.growth, true)}
                    </span>
                  )}
                </div>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-500 rounded-full transition-all"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================
// State Components
// ============================================

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      <p className="mt-3 text-sm text-gray-500">Loading details...</p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-3">
        <X className="w-6 h-6 text-red-600" />
      </div>
      <p className="text-sm font-medium text-gray-900">Failed to load details</p>
      <p className="text-xs text-gray-500 mt-1">{message}</p>
    </div>
  );
}

