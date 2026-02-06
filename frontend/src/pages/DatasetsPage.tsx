import { useState, useEffect } from 'react';
import { useProject } from '@/context/ProjectContext';
import { datasetsService } from '@/services/datasets';
import { Plus, Database, AlertCircle, Upload, Eye, Trash2, FileSpreadsheet } from 'lucide-react';
import DatasetPreviewModal from '@/components/DatasetPreviewModal';
import type { Dataset } from '@/types';

export default function DatasetsPage() {
  const { activeProject } = useProject();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  useEffect(() => {
    loadDatasets();
  }, [activeProject?.id]);

  const loadDatasets = async () => {
    if (!activeProject) {
      setDatasets([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      const data = await datasetsService.list(activeProject.id);
      setDatasets(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Project</h3>
          <p className="text-gray-500">Please select a project to view datasets</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading datasets...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Datasets</h2>
          <p className="text-gray-500 mt-1">Manage your data sources</p>
        </div>
        <div className="flex gap-2">
          <a
            href="/upload"
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Upload className="w-5 h-5" />
            Upload File
          </a>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Plus className="w-5 h-5" />
            Add SQL Dataset
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {datasets.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No datasets yet</h3>
          <p className="text-gray-500 mb-6">Add your first dataset to get started</p>
          <div className="flex justify-center gap-4">
            <a
              href="/upload"
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              <FileSpreadsheet className="w-5 h-5" />
              Upload CSV/Excel
            </a>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
              <Database className="w-5 h-5" />
              Connect SQL Database
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {datasets.map((dataset) => (
            <div
              key={dataset.id}
              className="p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow group"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {dataset.source_type === 'uploaded_file' ? (
                    <FileSpreadsheet className="w-5 h-5 text-green-500" />
                  ) : (
                    <Database className="w-5 h-5 text-blue-500" />
                  )}
                  <h3 className="text-lg font-semibold text-gray-900">{dataset.name}</h3>
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    dataset.source_type === 'uploaded_file'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {dataset.source_type === 'uploaded_file' ? 'File' : 'SQL'}
                </span>
              </div>
              
              {dataset.description && (
                <p className="text-sm text-gray-500 mb-4">{dataset.description}</p>
              )}
              
              <div className="space-y-1 text-xs text-gray-400 mb-4">
                <div>Table: <span className="font-mono">{dataset.table_name}</span></div>
                <div>Grain: {dataset.grain}</div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => setSelectedDataset(dataset)}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  <Eye className="w-4 h-4" />
                  Preview
                </button>
                <button className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100">
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {selectedDataset && (
        <DatasetPreviewModal
          dataset={selectedDataset}
          onClose={() => setSelectedDataset(null)}
        />
      )}
    </div>
  );
}
