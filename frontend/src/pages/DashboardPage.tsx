import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useProject } from '@/context/ProjectContext';
import { dashboardsService } from '@/services/dashboards';
import { LayoutDashboard, AlertCircle, Plus, Eye, Edit, Trash2, Clock } from 'lucide-react';
import type { Dashboard } from '@/types';

export default function DashboardPage() {
  const { activeProject } = useProject();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboards();
  }, [activeProject?.id]);

  const loadDashboards = async () => {
    if (!activeProject) {
      setDashboards([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      const data = await dashboardsService.list(activeProject.id);
      setDashboards(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboards');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this dashboard?')) return;

    try {
      await dashboardsService.delete(id);
      await loadDashboards();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete dashboard');
    }
  };

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Project</h3>
          <p className="text-gray-500">Please select a project to view dashboards</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading dashboards...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboards</h2>
          <p className="text-gray-500 mt-1">View and manage your analytics dashboards</p>
        </div>
        <Link
          to="/dashboards/new"
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create Dashboard
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {dashboards.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <LayoutDashboard className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No dashboards yet</h3>
          <p className="text-gray-500 mb-6">Create your first dashboard to visualize your data</p>
          <Link
            to="/dashboards/new"
            className="inline-flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="w-5 h-5" />
            Create Your First Dashboard
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((dashboard) => (
            <div
              key={dashboard.id}
              className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow overflow-hidden group"
            >
              {/* Dashboard Preview Area */}
              <div className="h-32 bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center">
                <LayoutDashboard className="w-12 h-12 text-primary-300" />
              </div>

              {/* Dashboard Info */}
              <div className="p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{dashboard.name}</h3>
                {dashboard.description && (
                  <p className="text-sm text-gray-500 mb-3 line-clamp-2">{dashboard.description}</p>
                )}

                <div className="flex items-center gap-4 text-xs text-gray-400 mb-4">
                  <span className="flex items-center gap-1">
                    <LayoutDashboard className="w-3 h-3" />
                    {dashboard.visuals?.length || 0} visuals
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(dashboard.updated_at).toLocaleDateString()}
                  </span>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Link
                    to={`/dashboards/${dashboard.id}`}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
                  >
                    <Eye className="w-4 h-4" />
                    View
                  </Link>
                  <Link
                    to={`/dashboards/${dashboard.id}/edit`}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-primary-50 text-primary-700 rounded hover:bg-primary-100 text-sm"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDelete(dashboard.id)}
                    className="px-3 py-2 bg-red-50 text-red-600 rounded hover:bg-red-100"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
