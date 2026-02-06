import { useState, useEffect } from 'react';
import { useProject } from '@/context/ProjectContext';
import { datasetsService } from '@/services/datasets';
import { queryService } from '@/services/query';
import {
  AlertCircle,
  BarChart3,
  LineChart,
  PieChart,
  Table2,
  TrendingUp,
  Play,
  Loader2,
  Plus,
  X,
  Filter as FilterIcon,
  Calendar,
  Hash,
  Tags,
} from 'lucide-react';
import type { Dataset, SemanticDefinition, VisualType, MeasureConfig, Filter } from '@/types';

interface VisualConfig {
  type: VisualType;
  dimensions: string[];
  measures: MeasureConfig[];
  filters: Filter[];
  timeGrain?: string;
  limit: number;
}

const VISUAL_TYPES: { type: VisualType; label: string; icon: typeof BarChart3 }[] = [
  { type: 'kpi', label: 'KPI Card', icon: TrendingUp },
  { type: 'bar', label: 'Bar Chart', icon: BarChart3 },
  { type: 'line', label: 'Line Chart', icon: LineChart },
  { type: 'pie', label: 'Pie Chart', icon: PieChart },
  { type: 'table', label: 'Table', icon: Table2 },
];

const AGGREGATIONS = ['sum', 'avg', 'count', 'min', 'max'];

export default function VisualBuilderPage() {
  const { activeProject } = useProject();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [semantic, setSemantic] = useState<SemanticDefinition | null>(null);
  const [loading, setLoading] = useState(true);
  const [queryLoading, setQueryLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<Record<string, any>[]>([]);

  const [config, setConfig] = useState<VisualConfig>({
    type: 'bar',
    dimensions: [],
    measures: [],
    filters: [],
    limit: 100,
  });

  useEffect(() => {
    loadDatasets();
  }, [activeProject?.id]);

  useEffect(() => {
    if (selectedDataset) {
      loadSemantic();
    }
  }, [selectedDataset?.id]);

  const loadDatasets = async () => {
    if (!activeProject) {
      setDatasets([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await datasetsService.list(activeProject.id);
      setDatasets(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const loadSemantic = async () => {
    if (!selectedDataset) return;

    try {
      const data = await datasetsService.getSemantic(selectedDataset.id);
      setSemantic(data);
    } catch (err) {
      setSemantic(null);
    }
  };

  const addDimension = (dim: string) => {
    if (!config.dimensions.includes(dim)) {
      setConfig({ ...config, dimensions: [...config.dimensions, dim] });
    }
  };

  const removeDimension = (dim: string) => {
    setConfig({ ...config, dimensions: config.dimensions.filter((d) => d !== dim) });
  };

  const addMeasure = (name: string, column: string) => {
    const newMeasure: MeasureConfig = {
      name,
      column,
      aggregation: 'sum',
    };
    setConfig({ ...config, measures: [...config.measures, newMeasure] });
  };

  const updateMeasureAggregation = (index: number, aggregation: string) => {
    const newMeasures = [...config.measures];
    newMeasures[index] = { ...newMeasures[index], aggregation };
    setConfig({ ...config, measures: newMeasures });
  };

  const removeMeasure = (index: number) => {
    setConfig({ ...config, measures: config.measures.filter((_, i) => i !== index) });
  };

  const runQuery = async () => {
    if (!selectedDataset) return;

    try {
      setQueryLoading(true);
      setError('');

      const response = await queryService.execute({
        dataset_id: selectedDataset.id,
        dimensions: config.dimensions,
        measures: config.measures,
        filters: config.filters,
        limit: config.limit,
      });

      setResults(response.results || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Query failed');
      setResults([]);
    } finally {
      setQueryLoading(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Project</h3>
          <p className="text-gray-500">Please select a project to build visuals</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* Left Panel - Configuration */}
      <div className="w-80 border-r border-gray-200 bg-gray-50 overflow-y-auto">
        <div className="p-4 space-y-6">
          {/* Dataset Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Dataset</label>
            <select
              value={selectedDataset?.id || ''}
              onChange={(e) => {
                const ds = datasets.find((d) => d.id === e.target.value);
                setSelectedDataset(ds || null);
                setConfig({ ...config, dimensions: [], measures: [] });
                setResults([]);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a dataset</option>
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name}
                </option>
              ))}
            </select>
          </div>

          {/* Visual Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Visual Type</label>
            <div className="grid grid-cols-3 gap-2">
              {VISUAL_TYPES.map((vt) => (
                <button
                  key={vt.type}
                  onClick={() => setConfig({ ...config, type: vt.type })}
                  className={`p-3 rounded-lg border transition-colors ${
                    config.type === vt.type
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <vt.icon className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-xs">{vt.label}</div>
                </button>
              ))}
            </div>
          </div>

          {selectedDataset && (
            <>
              {/* Dimensions */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <Tags className="w-4 h-4 text-blue-500" />
                  Dimensions
                </label>
                <div className="space-y-2">
                  {/* Selected Dimensions */}
                  {config.dimensions.map((dim) => (
                    <div
                      key={dim}
                      className="flex items-center justify-between px-3 py-2 bg-blue-50 rounded-lg"
                    >
                      <span className="text-sm text-blue-700">{dim}</span>
                      <button
                        onClick={() => removeDimension(dim)}
                        className="text-blue-500 hover:text-blue-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}

                  {/* Available Dimensions */}
                  <div className="border border-gray-200 rounded-lg p-2 max-h-32 overflow-y-auto">
                    {semantic?.dimensions?.map((dim) => (
                      <button
                        key={dim.name}
                        onClick={() => addDimension(dim.column)}
                        disabled={config.dimensions.includes(dim.column)}
                        className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {dim.name}
                      </button>
                    )) || (
                      <p className="text-xs text-gray-400 p-2">No semantic definition available</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Measures */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <Hash className="w-4 h-4 text-green-500" />
                  Measures
                </label>
                <div className="space-y-2">
                  {/* Selected Measures */}
                  {config.measures.map((measure, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 px-3 py-2 bg-green-50 rounded-lg"
                    >
                      <span className="text-sm text-green-700 flex-1">{measure.name}</span>
                      <select
                        value={measure.aggregation}
                        onChange={(e) => updateMeasureAggregation(idx, e.target.value)}
                        className="text-xs px-2 py-1 border border-green-200 rounded"
                      >
                        {AGGREGATIONS.map((agg) => (
                          <option key={agg} value={agg}>
                            {agg.toUpperCase()}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => removeMeasure(idx)}
                        className="text-green-500 hover:text-green-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}

                  {/* Available Measures */}
                  <div className="border border-gray-200 rounded-lg p-2 max-h-32 overflow-y-auto">
                    {semantic?.measures?.map((m) => (
                      <button
                        key={m.name}
                        onClick={() => addMeasure(m.name, m.column)}
                        className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 rounded"
                      >
                        {m.name}
                      </button>
                    )) || (
                      <p className="text-xs text-gray-400 p-2">No semantic definition available</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Filters */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <FilterIcon className="w-4 h-4 text-orange-500" />
                  Filters
                </label>
                <button className="w-full px-3 py-2 border border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-gray-400 hover:bg-gray-50 flex items-center justify-center gap-2">
                  <Plus className="w-4 h-4" />
                  Add Filter
                </button>
              </div>

              {/* Time Grain */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-purple-500" />
                  Time Grain
                </label>
                <select
                  value={config.timeGrain || ''}
                  onChange={(e) => setConfig({ ...config, timeGrain: e.target.value || undefined })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">Auto</option>
                  <option value="day">Daily</option>
                  <option value="week">Weekly</option>
                  <option value="month">Monthly</option>
                  <option value="year">Yearly</option>
                </select>
              </div>

              {/* Run Query Button */}
              <button
                onClick={runQuery}
                disabled={queryLoading || config.measures.length === 0}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {queryLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Run Query
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Right Panel - Preview */}
      <div className="flex-1 overflow-auto p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Visual Builder</h2>
        
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {!selectedDataset ? (
          <div className="flex items-center justify-center h-64 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Select a dataset to start building your visualization</p>
            </div>
          </div>
        ) : results.length === 0 ? (
          <div className="flex items-center justify-center h-64 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
            <div className="text-center">
              <Play className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Add measures and click "Run Query" to see results</p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {/* Results Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {Object.keys(results[0] || {}).map((col) => (
                      <th
                        key={col}
                        className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {results.slice(0, 50).map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      {Object.values(row).map((val, colIdx) => (
                        <td key={colIdx} className="px-4 py-2 text-sm text-gray-900">
                          {val != null ? String(val) : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 bg-gray-50 text-xs text-gray-500">
              Showing {Math.min(results.length, 50)} of {results.length} rows
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

