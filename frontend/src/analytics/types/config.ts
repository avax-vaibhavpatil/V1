/**
 * Analytics Dashboard Configuration Types
 * 
 * These types define the config-driven architecture for the reporting dashboard.
 * All reports are defined via JSON configuration using these interfaces.
 * 
 * Updated: Supports PostgreSQL database queries and extended features
 */

// ============================================
// Filter Configuration Types
// ============================================

export type FilterType = 'single' | 'multi';
export type FilterUI = 'tabs' | 'chips' | 'select' | 'multiselect' | 'daterange';
export type OptionsSource = 'static' | 'api';

export interface FilterOption {
  label: string;
  value: string;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: FilterType;
  ui: FilterUI;
  optionsSource: OptionsSource;
  options?: FilterOption[];
  endpoint?: string;
  dependsOn?: string[];
  defaultValue?: string | string[];
  searchable?: boolean;
  placeholder?: string;
  dbColumn?: string; // Database column name for filtering
}

// ============================================
// Time Configuration Types
// ============================================

export interface TimeDefaults {
  fiscalYear: string;
  period: string;
}

export interface ToggleDefaults {
  aggregation: 'YTD' | 'QTD' | 'MTD';
  metricMode: 'VALUE' | 'VOLUME' | 'UNITS';
}

export interface SegmentDefaults {
  [key: string]: string;
}

export interface ReportDefaults {
  time: TimeDefaults;
  toggles: ToggleDefaults;
  segments: SegmentDefaults;
}

// ============================================
// KPI Configuration Types
// ============================================

export type KpiClickActionType = 'filter' | 'highlight' | 'drilldown';

export interface KpiClickAction {
  type: KpiClickActionType;
  filterKey?: string;
  value?: string;
  groupKey?: string;
}

export interface KpiCardConfig {
  id: string;
  title: string;
  icon?: string;
  primaryMetric: string;
  secondaryMetric?: string | null;
  shareMetric?: string | null;
  trendMetric?: string | null;
  onClick?: KpiClickAction;
  tooltip?: string;
  dbFilter?: string; // SQL WHERE clause for this KPI
  highlight?: boolean; // Whether to highlight this KPI card
}

export interface KpiConfig {
  cards: KpiCardConfig[];
}

// ============================================
// Table Configuration Types
// ============================================

export type FormatType = 
  | 'currency' 
  | 'currencyCr' 
  | 'currencyLakh' 
  | 'percent' 
  | 'integer' 
  | 'decimal' 
  | 'decimal2'  // 2 decimal places
  | 'compact';

export type ConditionalStyle = 'posNeg' | 'heatmap' | 'threshold';

export interface ColumnConfig {
  key: string;
  label: string;
  format?: FormatType;
  conditional?: ConditionalStyle;
  width?: number;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  tooltip?: string;
  dbExpression?: string; // SQL expression for this column
}

export interface ColumnGroupConfig {
  groupLabel: string;
  groupKey: string;
  columns: ColumnConfig[];
  dbFilter?: string; // SQL WHERE clause for this column group
  highlight?: boolean; // Whether to highlight this group
}

export interface EntityColumnConfig {
  key: string;
  label: string;
  pinned: boolean;
  secondaryKey?: string;
  secondaryLabel?: string;
  dbColumn?: string; // Database column name
}

export interface EntityViewMode {
  key: string;
  label: string;
}

export interface SummaryRowConfig {
  enabled: boolean;
  label: string;
  position: 'top' | 'bottom';
}

export interface TableConfig {
  entityColumn: EntityColumnConfig;
  columnGroups: ColumnGroupConfig[];
  defaultSort?: {
    key: string;
    direction: 'asc' | 'desc';
  };
  pageSize?: number;
  virtualScroll?: boolean;
  entityViewModes?: EntityViewMode[]; // Alternative view modes
  summaryRow?: SummaryRowConfig; // Summary row configuration
}

// ============================================
// Drilldown Configuration Types
// ============================================

export type DrilldownWidget = 
  | 'entitySummary' 
  | 'trendChart' 
  | 'breakdownByCategory' 
  | 'breakdownByProduct' 
  | 'transactionsList'
  | 'topCustomers'
  | 'materialMix';

export interface DrilldownLevel {
  key: string;
  label: string;
  nextLevel: string | null;
}

export interface DrilldownConfig {
  enabled: boolean;
  widgets: DrilldownWidget[];
  triggerColumn?: string;
  drilldownLevels?: DrilldownLevel[];
}

// ============================================
// Conditional Formatting Rules
// ============================================

export interface ConditionalStyleRule {
  positive?: { color?: string; icon?: string; bgColor?: string };
  negative?: { color?: string; icon?: string; bgColor?: string };
  zero?: { color?: string; icon?: string; bgColor?: string };
}

export interface ThresholdRule {
  thresholds: { value: number; color: string }[];
}

export interface NumberFormatConfig {
  decimals: number;
  thousandsSeparator?: boolean;
  suffix?: string;
}

export interface FormatRules {
  conditionalStyles: {
    posNeg?: ConditionalStyleRule;
    heatmap?: ThresholdRule;
    threshold?: ThresholdRule;
  };
  currency?: {
    symbol: string;
    scale: 'Cr' | 'Lakh' | 'K' | 'M';
    scaleFactors?: {
      [key: string]: number;
    };
  };
  number?: {
    [key: string]: NumberFormatConfig;
  };
}

// ============================================
// Database Configuration
// ============================================

export interface DbMetricsConfig {
  [metricName: string]: string; // metric name -> SQL expression
}

export interface DbDimensionsConfig {
  [dimensionName: string]: string; // dimension name -> column name
}

export interface DbConfig {
  tableName: string;
  dateColumn: string;
  periodColumn: string;
  metrics: DbMetricsConfig;
  dimensions: DbDimensionsConfig;
}

// ============================================
// Data Endpoints Configuration
// ============================================

export interface DataEndpoints {
  meta: string;
  kpis: string;
  table: string;
  drilldown: string;
  export?: string;
}

export interface DataConfig {
  endpoints: DataEndpoints;
  dbConfig?: DbConfig; // Database configuration for backend queries
}

// ============================================
// Query Templates (for backend)
// ============================================

export interface QueryTemplates {
  tableQuery?: string;
  kpiQuery?: string;
  drilldownQuery?: string;
}

// ============================================
// Features/Permissions Configuration
// ============================================

export interface FeaturesConfig {
  export?: boolean;
  drilldown?: boolean;
  share?: boolean;
  refresh?: boolean;
  print?: boolean;
  columnToggle?: boolean;
  viewModeSwitch?: boolean;
}

// ============================================
// Main Report Configuration
// ============================================

export interface ReportConfig {
  reportId: string;
  title: string;
  description?: string;
  defaults: ReportDefaults;
  data: DataConfig;
  filters: FilterConfig[];
  kpis: KpiConfig;
  table: TableConfig;
  formatRules: FormatRules;
  drilldown: DrilldownConfig;
  features?: FeaturesConfig;
  queryTemplates?: QueryTemplates; // SQL query templates for backend
}

// ============================================
// API Response Types
// ============================================

export interface MetaResponse {
  lastUpdatedAt: string;
  features: FeaturesConfig;
  allowed?: {
    [filterKey: string]: string[];
  };
}

export interface KpiCardData {
  id: string;
  [metricKey: string]: string | number | null;
}

export interface KpisResponse {
  cards: KpiCardData[];
}

export interface TableRow {
  entityId: string;
  entityName: string;
  entityCode?: string;
  [columnKey: string]: string | number | undefined | null;
}

export interface TableResponse {
  rows: TableRow[];
  page: number;
  pageSize: number;
  total: number;
  summary?: TableRow; // Summary row data
}

export interface TrendDataPoint {
  period: string;
  value: number;
  target?: number;
}

export interface BreakdownItem {
  name: string;
  value: number;
  percentage: number;
  growth?: number;
}

export interface DrilldownResponse {
  entity: {
    id: string;
    name: string;
    code?: string;
  };
  summary: {
    [metricKey: string]: number;
  };
  trend: TrendDataPoint[];
  breakdown: {
    [categoryKey: string]: BreakdownItem[];
  };
}

// ============================================
// Filter State Types
// ============================================

export interface FilterState {
  [filterKey: string]: string | string[] | undefined;
}

export interface TimeState {
  fiscalYear: string;
  period: string;
}

export interface ToggleState {
  aggregation: 'YTD' | 'QTD' | 'MTD';
  metricMode: 'VALUE' | 'VOLUME' | 'UNITS';
}

export interface AppliedFilters {
  filters: FilterState;
  time: TimeState;
  toggles: ToggleState;
}
