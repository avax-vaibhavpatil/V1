// Backend API types matching the FastAPI models

export interface Project {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface Dataset {
  id: string;
  project_id?: number;
  name: string;
  description?: string;
  table_name: string;
  schema_name?: string;
  grain: string;
  source_type: 'sql' | 'uploaded_file';
  uploaded_file_id?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface SemanticDefinition {
  grain: string;
  time_columns: string[];
  dimensions: Dimension[];
  measures: Measure[];
}

export interface Dimension {
  name: string;
  column: string;
  type: string;
  description?: string;
}

export interface Measure {
  name: string;
  column: string;
  type: string;
  aggregations: string[];
  format?: string;
  description?: string;
}

export interface Dashboard {
  id: number;
  project_id?: number;
  name: string;
  description?: string;
  layout_config: LayoutConfig;
  is_active: boolean;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
  visuals?: DashboardVisual[];
}

export interface DashboardVisual {
  id: number;
  dashboard_id: number;
  visual_type: VisualType;
  visual_config: VisualConfig;
  position: Position;
  order: number;
  is_active: boolean;
}

export type VisualType = 'kpi' | 'line' | 'bar' | 'column' | 'stacked_bar' | 'table' | 'pie';

export interface VisualConfig {
  dimensions?: string[];
  measures?: MeasureConfig[];
  measure?: MeasureConfig; // For KPI
  filters?: Filter[];
  time_filter?: TimeFilter;
  sorting?: Sorting;
  time_grain?: string;
  limit?: number;
}

export interface MeasureConfig {
  name: string;
  column: string;
  aggregation: string;
  alias?: string;
}

export interface Filter {
  column: string;
  operator: '=' | '!=' | 'IN' | '>' | '<' | '>=' | '<=';
  value: any;
}

export interface TimeFilter {
  column: string;
  start_date?: string;
  end_date?: string;
}

export interface Sorting {
  field: string;
  order: 'asc' | 'desc';
}

export interface Position {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface LayoutConfig {
  columns: number;
  rows: number;
  cell_height?: number;
}

export interface DatabaseConnection {
  id: number;
  project_id: number;
  name: string;
  db_type: 'postgresql' | 'mysql';
  host: string;
  port: number;
  database: string;
  username: string;
  schema_name?: string;
  is_read_only: boolean;
  is_active: boolean;
  created_at: string;
}

export interface UploadedFile {
  id: number;
  project_id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  file_type: 'csv' | 'xlsx';
  row_count?: number;
  column_count?: number;
  is_processed: boolean;
  dataset_id?: string;
  created_at: string;
  created_by: string;
}

export interface QueryRequest {
  dataset_id: string;
  dimensions: string[];
  measures: MeasureConfig[];
  filters?: Filter[];
  time_filter?: TimeFilter;
  limit?: number;
}

export interface QueryResponse {
  query: string;
  results: Record<string, any>[];
  row_count: number;
}

export interface CalculationValidation {
  is_valid: boolean;
  error_message?: string;
  validation_result?: {
    formula: string;
    is_valid: boolean;
    fields_used: string[];
  };
}

export interface DependencyUsage {
  dataset_id: string;
  dataset_name: string;
  used_in_dashboards: number;
  used_in_calculations: number;
  can_delete: boolean;
  warnings: string[];
}

export interface LLMMetadata {
  id?: number;
  user_question: string;
  tokens_used: number | null;
  created_at?: string;
}

export interface TokenStatistics {
  total_queries: number;
  total_tokens: number;
  avg_tokens: number;
  min_tokens: number;
  max_tokens: number;
}


