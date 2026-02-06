import { useState, useEffect } from 'react';
import { X, Table, Tags, BarChart3, Calendar, Hash, Type, Loader2 } from 'lucide-react';
import { datasetsService } from '@/services/datasets';
import type { Dataset, SemanticDefinition } from '@/types';

interface DatasetPreviewModalProps {
  dataset: Dataset;
  onClose: () => void;
}

type TabType = 'preview' | 'semantic' | 'schema';

export default function DatasetPreviewModal({ dataset, onClose }: DatasetPreviewModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('preview');
  const [previewData, setPreviewData] = useState<Record<string, unknown>[]>([]);
  const [semantic, setSemantic] = useState<SemanticDefinition | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [previewSource, setPreviewSource] = useState<'file' | 'sql' | null>(null);

  useEffect(() => {
    loadData();
  }, [dataset.id, activeTab]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      if (activeTab === 'preview') {
        // Load preview data using the new preview endpoint
        try {
          const response = await datasetsService.preview(dataset.id, 100);
          setPreviewData(response.results || []);
          setPreviewSource(response.source);
        } catch (e: unknown) {
          // If preview fails, show empty preview with error
          setPreviewData([]);
          const err = e as { response?: { data?: { detail?: string } } };
          setError(err.response?.data?.detail || 'Failed to load preview data');
        }
      } else if (activeTab === 'semantic') {
        // Load semantic definition
        const semanticData = await datasetsService.getSemantic(dataset.id);
        setSemantic(semanticData);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'preview' as TabType, label: 'Data Preview', icon: Table },
    { id: 'semantic' as TabType, label: 'Semantic Schema', icon: Tags },
    { id: 'schema' as TabType, label: 'Table Info', icon: Hash },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{dataset.name}</h2>
            <p className="text-sm text-gray-500 mt-1">{dataset.description || 'No description'}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-500">{error}</div>
          ) : (
            <>
              {/* Preview Tab */}
              {activeTab === 'preview' && (
                <div className="overflow-auto">
                  {previewData.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      No preview data available
                    </div>
                  ) : (
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(previewData[0] || {}).map((col) => (
                            <th
                              key={col}
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {previewData.slice(0, 50).map((row, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            {Object.values(row).map((val, colIdx) => (
                              <td
                                key={colIdx}
                                className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap"
                              >
                                {val != null ? String(val) : '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  <div className="flex items-center justify-between mt-4">
                    <p className="text-xs text-gray-400">
                      Showing {Math.min(previewData.length, 50)} of {previewData.length} rows
                    </p>
                    {previewSource && (
                      <span className={`text-xs px-2 py-1 rounded ${
                        previewSource === 'file' 
                          ? 'bg-blue-100 text-blue-700' 
                          : 'bg-green-100 text-green-700'
                      }`}>
                        Source: {previewSource === 'file' ? 'Uploaded File' : 'SQL Table'}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Semantic Tab */}
              {activeTab === 'semantic' && (
                <div className="space-y-6">
                  {semantic ? (
                    <>
                      {/* Dimensions */}
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                          <Tags className="w-5 h-5 text-blue-500" />
                          Dimensions
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {semantic.dimensions?.map((dim) => (
                            <div
                              key={dim.name}
                              className="p-4 bg-blue-50 rounded-lg border border-blue-100"
                            >
                              <div className="flex items-center gap-2 mb-1">
                                <Type className="w-4 h-4 text-blue-600" />
                                <span className="font-medium text-blue-900">{dim.name}</span>
                              </div>
                              <div className="text-sm text-blue-700">Column: {dim.column}</div>
                              <div className="text-xs text-blue-500">Type: {dim.type}</div>
                              {dim.description && (
                                <p className="text-xs text-blue-600 mt-1">{dim.description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Measures */}
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                          <BarChart3 className="w-5 h-5 text-green-500" />
                          Measures
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {semantic.measures?.map((measure) => (
                            <div
                              key={measure.name}
                              className="p-4 bg-green-50 rounded-lg border border-green-100"
                            >
                              <div className="flex items-center gap-2 mb-1">
                                <Hash className="w-4 h-4 text-green-600" />
                                <span className="font-medium text-green-900">{measure.name}</span>
                              </div>
                              <div className="text-sm text-green-700">Column: {measure.column}</div>
                              <div className="text-xs text-green-500">
                                Aggregations: {measure.aggregations?.join(', ')}
                              </div>
                              {measure.description && (
                                <p className="text-xs text-green-600 mt-1">{measure.description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Time Columns */}
                      {semantic.time_columns?.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-purple-500" />
                            Time Columns
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {semantic.time_columns.map((col) => (
                              <span
                                key={col}
                                className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm"
                              >
                                {col}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      No semantic definition found for this dataset
                    </div>
                  )}
                </div>
              )}

              {/* Schema Tab */}
              {activeTab === 'schema' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-500">Table Name</div>
                      <div className="font-mono text-gray-900">{dataset.table_name}</div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-500">Schema</div>
                      <div className="font-mono text-gray-900">{dataset.schema_name || 'default'}</div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-500">Grain</div>
                      <div className="font-mono text-gray-900">{dataset.grain}</div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-500">Source Type</div>
                      <div className="font-mono text-gray-900">{dataset.source_type}</div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-500">Created At</div>
                      <div className="font-mono text-gray-900">
                        {new Date(dataset.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-500">Status</div>
                      <div className={`font-medium ${dataset.is_active ? 'text-green-600' : 'text-red-600'}`}>
                        {dataset.is_active ? 'Active' : 'Inactive'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

