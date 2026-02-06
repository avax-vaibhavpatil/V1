/**
 * KpiCard Component
 * 
 * Displays a single KPI metric card with:
 * - Title and optional icon
 * - Primary metric (actual value)
 * - Secondary metric (target/previous period)
 * - Contribution/share percentage
 * - Trend indicator with color
 */

import { TrendingUp, TrendingDown, Minus, Zap, Cable, Lightbulb, Box, Cpu, Lamp } from 'lucide-react';
import type { KpiCardConfig, KpiCardData, KpiClickAction, FormatRules } from '../types';
import { formatCurrency, formatPercent, getConditionalStyle } from '../utils/formatters';

// ============================================
// Icon Mapping
// ============================================

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  projectWires: Cable,
  flexibles: Zap,
  hdc: Cpu,
  dowells: Box,
  fmeg: Lightbulb,
  lumes: Lamp,
};

// ============================================
// KpiCard Component
// ============================================

interface KpiCardProps {
  config: KpiCardConfig;
  data: KpiCardData;
  formatRules: FormatRules;
  isHighlighted?: boolean;
  onClick?: (action: KpiClickAction) => void;
}

export default function KpiCard({
  config,
  data,
  formatRules,
  isHighlighted,
  onClick,
}: KpiCardProps) {
  const Icon = CATEGORY_ICONS[config.id] || Zap;
  
  const primaryValue = data[config.primaryMetric] as number || 0;
  const secondaryValue = config.secondaryMetric ? (data[config.secondaryMetric] as number || 0) : undefined;
  const shareValue = config.shareMetric ? (data[config.shareMetric] as number || 0) : undefined;
  const trendValue = config.trendMetric ? (data[config.trendMetric] as number || 0) : undefined;
  
  // Get conditional styling for trend
  const trendStyle = trendValue !== undefined
    ? getConditionalStyle(trendValue, formatRules.conditionalStyles.posNeg)
    : null;
  
  const handleClick = () => {
    if (onClick && config.onClick) {
      onClick(config.onClick);
    }
  };
  
  return (
    <div
      onClick={handleClick}
      className={`relative p-4 bg-white rounded-xl border transition-all cursor-pointer ${
        isHighlighted
          ? 'border-indigo-500 ring-2 ring-indigo-200'
          : 'border-gray-200 hover:border-indigo-300 hover:shadow-md'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 rounded-lg">
            <Icon className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">{config.title}</h3>
            {config.tooltip && (
              <p className="text-xs text-gray-500">{config.tooltip}</p>
            )}
          </div>
        </div>
        
        {/* Contribution Badge */}
        {shareValue !== undefined && (
          <div className="px-2 py-1 bg-gray-100 rounded-full">
            <span className="text-xs font-medium text-gray-600">
              {formatPercent(shareValue)}
            </span>
          </div>
        )}
      </div>
      
      {/* Primary Metric */}
      <div className="mb-2">
        <div className="text-2xl font-bold text-gray-900">
          {formatCurrency(primaryValue)}
        </div>
        <div className="text-xs text-gray-500">Actual Sales</div>
      </div>
      
      {/* Secondary and Trend Row */}
      <div className="flex items-center justify-between">
        {/* Secondary Metric (Target) */}
        {secondaryValue !== undefined && (
          <div>
            <div className="text-sm text-gray-600">
              Target: {formatCurrency(secondaryValue)}
            </div>
          </div>
        )}
        
        {/* Trend Indicator */}
        {trendValue !== undefined && trendStyle && (
          <div
            className="flex items-center gap-1 px-2 py-1 rounded-full"
            style={{ backgroundColor: `${trendStyle.color}15` }}
          >
            {trendStyle.icon === 'arrowUp' && (
              <TrendingUp className="w-4 h-4" style={{ color: trendStyle.color }} />
            )}
            {trendStyle.icon === 'arrowDown' && (
              <TrendingDown className="w-4 h-4" style={{ color: trendStyle.color }} />
            )}
            {trendStyle.icon === 'dash' && (
              <Minus className="w-4 h-4" style={{ color: trendStyle.color }} />
            )}
            <span
              className="text-sm font-semibold"
              style={{ color: trendStyle.color }}
            >
              {formatPercent(trendValue, true)}
            </span>
          </div>
        )}
      </div>
      
      {/* Click Indicator */}
      {config.onClick && (
        <div className="absolute bottom-2 right-2 text-gray-300">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      )}
    </div>
  );
}

// ============================================
// KpiGrid Component
// ============================================

interface KpiGridProps {
  configs: KpiCardConfig[];
  data: KpiCardData[];
  formatRules: FormatRules;
  highlightedCategory?: string;
  onCardClick?: (action: KpiClickAction) => void;
  isLoading?: boolean;
}

export function KpiGrid({
  configs,
  data,
  formatRules,
  highlightedCategory,
  onCardClick,
  isLoading,
}: KpiGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 p-6">
        {configs.map(config => (
          <KpiCardSkeleton key={config.id} />
        ))}
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 p-6 bg-gray-50">
      {configs.map(config => {
        const cardData = data.find(d => d.id === config.id) || { id: config.id };
        return (
          <KpiCard
            key={config.id}
            config={config}
            data={cardData}
            formatRules={formatRules}
            isHighlighted={highlightedCategory === config.id}
            onClick={onCardClick}
          />
        );
      })}
    </div>
  );
}

// ============================================
// Skeleton Loading State
// ============================================

function KpiCardSkeleton() {
  return (
    <div className="p-4 bg-white rounded-xl border border-gray-200 animate-pulse">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-9 h-9 bg-gray-200 rounded-lg" />
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-20 mb-1" />
          <div className="h-3 bg-gray-100 rounded w-16" />
        </div>
      </div>
      <div className="h-8 bg-gray-200 rounded w-24 mb-2" />
      <div className="h-3 bg-gray-100 rounded w-16 mb-3" />
      <div className="flex justify-between">
        <div className="h-4 bg-gray-100 rounded w-20" />
        <div className="h-6 bg-gray-200 rounded-full w-16" />
      </div>
    </div>
  );
}

