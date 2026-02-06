/**
 * Value Formatters for Analytics Dashboard
 * 
 * Provides consistent formatting for currencies, percentages, and numbers.
 * Updated: Supports real database values (not pre-scaled)
 */

import type { FormatType, ConditionalStyleRule } from '../types';

// ============================================
// Scale Factors for Currency Conversion
// ============================================

const SCALE_FACTORS = {
  Cr: 10000000,   // 1 Crore = 10 million
  Lakh: 100000,   // 1 Lakh = 100 thousand
  K: 1000,        // 1K = 1 thousand
  M: 1000000,     // 1M = 1 million
};

// ============================================
// Number Formatting
// ============================================

/**
 * Format currency value - handles raw values from database
 * Automatically converts to appropriate scale (Cr, Lakh, K)
 */
export function formatCurrency(value: number, scale: 'Cr' | 'Lakh' | 'K' | 'M' = 'Cr'): string {
  if (value === 0 || value === null || value === undefined) return '₹0';
  
  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  
  // For 'Cr' scale, convert from raw rupees to crores
  if (scale === 'Cr') {
    const crValue = absValue / SCALE_FACTORS.Cr;
    
    if (crValue >= 100) {
      return `${sign}₹${crValue.toFixed(0)} Cr`;
    } else if (crValue >= 10) {
      return `${sign}₹${crValue.toFixed(1)} Cr`;
    } else if (crValue >= 1) {
      return `${sign}₹${crValue.toFixed(2)} Cr`;
    } else if (crValue >= 0.01) {
      // Show in Lakhs if less than 1 Cr
      const lakhValue = absValue / SCALE_FACTORS.Lakh;
      return `${sign}₹${lakhValue.toFixed(2)} L`;
    } else {
      // Show in thousands if very small
      const kValue = absValue / SCALE_FACTORS.K;
      return `${sign}₹${kValue.toFixed(1)} K`;
    }
  }
  
  // For other scales
  const scaledValue = absValue / SCALE_FACTORS[scale];
  const suffix = scale === 'Lakh' ? ' L' : ` ${scale}`;
  
  if (scaledValue >= 100) {
    return `${sign}₹${scaledValue.toFixed(0)}${suffix}`;
  } else if (scaledValue >= 10) {
    return `${sign}₹${scaledValue.toFixed(1)}${suffix}`;
  } else {
    return `${sign}₹${scaledValue.toFixed(2)}${suffix}`;
  }
}

/**
 * Format currency in Crores from raw value
 */
export function formatCurrencyCr(value: number): string {
  return formatCurrency(value, 'Cr');
}

/**
 * Format currency in Lakhs from raw value
 */
export function formatCurrencyLakh(value: number): string {
  return formatCurrency(value, 'Lakh');
}

/**
 * Format percentage value
 */
export function formatPercent(value: number, showSign: boolean = false): string {
  if (value === 0 || value === null || value === undefined) return '0%';
  
  const sign = showSign && value > 0 ? '+' : '';
  const formatted = value.toFixed(1).replace(/\.0$/, '');
  return `${sign}${formatted}%`;
}

/**
 * Format as integer with Indian number formatting
 */
export function formatInteger(value: number): string {
  if (value === null || value === undefined) return '0';
  return new Intl.NumberFormat('en-IN').format(Math.round(value));
}

/**
 * Format as decimal with specified precision
 */
export function formatDecimal(value: number, decimals: number = 2): string {
  if (value === null || value === undefined) return '0';
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format as decimal with 2 decimal places
 */
export function formatDecimal2(value: number): string {
  return formatDecimal(value, 2);
}

/**
 * Format as compact number (auto-scale)
 */
export function formatCompact(value: number): string {
  if (value === null || value === undefined) return '0';
  
  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  
  if (absValue >= 10000000) {
    return `${sign}${(absValue / 10000000).toFixed(1)} Cr`;
  } else if (absValue >= 100000) {
    return `${sign}${(absValue / 100000).toFixed(1)} L`;
  } else if (absValue >= 1000) {
    return `${sign}${(absValue / 1000).toFixed(1)} K`;
  }
  return `${sign}${absValue.toFixed(0)}`;
}

// ============================================
// Generic Format Dispatcher
// ============================================

export function formatValue(value: number | string | undefined | null, format?: FormatType): string {
  if (value === undefined || value === null) return '-';
  
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numValue)) {
    return typeof value === 'string' ? value : '-';
  }
  
  switch (format) {
    case 'currency':
    case 'currencyCr':
      return formatCurrencyCr(numValue);
    case 'currencyLakh':
      return formatCurrencyLakh(numValue);
    case 'percent':
      return formatPercent(numValue, true);
    case 'integer':
      return formatInteger(numValue);
    case 'decimal':
      return formatDecimal(numValue);
    case 'decimal2':
      return formatDecimal2(numValue);
    case 'compact':
      return formatCompact(numValue);
    default:
      // Auto-detect: large numbers get currency treatment
      if (Math.abs(numValue) > 100000) {
        return formatCompact(numValue);
      }
      return formatDecimal(numValue);
  }
}

// ============================================
// Conditional Styling
// ============================================

export interface ConditionalStyleResult {
  color?: string;
  bgColor?: string;
  icon?: 'arrowUp' | 'arrowDown' | 'dash' | null;
}

export function getConditionalStyle(
  value: number,
  rule?: ConditionalStyleRule
): ConditionalStyleResult {
  if (!rule) return {};
  
  if (value > 0) {
    return {
      color: rule.positive?.color || '#16a34a', // green-600
      bgColor: rule.positive?.bgColor,
      icon: (rule.positive?.icon as ConditionalStyleResult['icon']) || 'arrowUp',
    };
  } else if (value < 0) {
    return {
      color: rule.negative?.color || '#dc2626', // red-600
      bgColor: rule.negative?.bgColor,
      icon: (rule.negative?.icon as ConditionalStyleResult['icon']) || 'arrowDown',
    };
  } else {
    return {
      color: rule.zero?.color || '#6b7280', // gray-500
      bgColor: rule.zero?.bgColor,
      icon: (rule.zero?.icon as ConditionalStyleResult['icon']) || 'dash',
    };
  }
}

// ============================================
// Date/Time Formatting
// ============================================

export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return formatTimestamp(isoString);
}

// ============================================
// Abbreviation Tooltips
// ============================================

export const ABBREVIATIONS: Record<string, string> = {
  'Act': 'Actual Sales',
  'Sales': 'Sales Amount',
  'P/L': 'Profit/Loss',
  'Qty': 'Quantity Sold',
  'Margin%': 'Profit Margin Percentage',
  '%G': 'Growth Percentage (vs Previous Period)',
  '%Ach': 'Achievement Percentage (vs Target)',
  'Tgt': 'Target Sales',
  'Contrib': 'Contribution Percentage',
  'Weight (MT)': 'Metal Weight in Metric Tons',
  'Receivables': 'Outstanding Receivables',
  'YTD': 'Year to Date',
  'QTD': 'Quarter to Date',
  'MTD': 'Month to Date',
  // Product categories
  'Building Wires': 'Building Wires (Standard & C90)',
  'LT Cables': 'Low Tension Cables',
  'Flexibles': 'Flexible Cables (LDC)',
  'HT & EHV': 'High Tension & Extra High Voltage Cables',
};

export function getAbbreviationTooltip(abbr: string): string | undefined {
  return ABBREVIATIONS[abbr];
}



