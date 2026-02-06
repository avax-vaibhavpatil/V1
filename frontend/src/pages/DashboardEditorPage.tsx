import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject } from '@/context/ProjectContext';
import { dashboardsService } from '@/services/dashboards';
import {
  AlertCircle,
  Save,
  Plus,
  Loader2,
  GripVertical,
  Trash2,
  Settings,
  X,
  BarChart3,
  LineChart,
  PieChart,
  Table2,
  TrendingUp,
  Move,
} from 'lucide-react';
import type { Dashboard, DashboardVisual, VisualType, Position } from '@/types';

const VISUAL_TYPES: { type: VisualType; label: string; icon: typeof BarChart3 }[] = [
  { type: 'kpi', label: 'KPI Card', icon: TrendingUp },
  { type: 'bar', label: 'Bar Chart', icon: BarChart3 },
  { type: 'line', label: 'Line Chart', icon: LineChart },
  { type: 'pie', label: 'Pie Chart', icon: PieChart },
  { type: 'table', label: 'Table', icon: Table2 },
];

interface CanvasVisual {
  id: string;
  type: VisualType;
  title: string;
  position: Position;
  config: Record<string, any>;
}

export default function DashboardEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { activeProject } = useProject();
  
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [visuals, setVisuals] = useState<CanvasVisual[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  
  const [dashboardName, setDashboardName] = useState('');
  const [dashboardDescription, setDashboardDescription] = useState('');
  
  const [selectedVisual, setSelectedVisual] = useState<string | null>(null);
  const [showAddPanel, setShowAddPanel] = useState(false);
  const [dragging, setDragging] = useState<string | null>(null);

  const isNewDashboard = id === 'new';

  useEffect(() => {
    if (!isNewDashboard && id) {
      loadDashboard(parseInt(id));
    } else {
      setLoading(false);
      setDashboardName('New Dashboard');
    }
  }, [id]);

  const loadDashboard = async (dashboardId: number) => {
    try {
      setLoading(true);
      const data = await dashboardsService.get(dashboardId);
      setDashboard(data);
      setDashboardName(data.name);
      setDashboardDescription(data.description || '');
      
      // Convert dashboard visuals to canvas visuals
      if (data.visuals) {
        setVisuals(
          data.visuals.map((v) => ({
            id: `visual-${v.id}`,
            type: v.visual_type,
            title: v.visual_config.title || `${v.visual_type} Visual`,
            position: v.position,
            config: v.visual_config,
          }))
        );
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const addVisual = (type: VisualType) => {
    const newVisual: CanvasVisual = {
      id: `visual-${Date.now()}`,
      type,
      title: `New ${VISUAL_TYPES.find((v) => v.type === type)?.label || 'Visual'}`,
      position: {
        x: 0,
        y: visuals.length * 2,
        width: type === 'kpi' ? 3 : 6,
        height: type === 'kpi' ? 2 : 4,
      },
      config: {},
    };
    setVisuals([...visuals, newVisual]);
    setShowAddPanel(false);
    setSelectedVisual(newVisual.id);
  };

  const updateVisualPosition = (id: string, position: Partial<Position>) => {
    setVisuals(
      visuals.map((v) =>
        v.id === id ? { ...v, position: { ...v.position, ...position } } : v
      )
    );
  };

  const deleteVisual = (id: string) => {
    setVisuals(visuals.filter((v) => v.id !== id));
    if (selectedVisual === id) {
      setSelectedVisual(null);
    }
  };

  const handleSave = async () => {
    if (!activeProject || !dashboardName.trim()) {
      setError('Please provide a dashboard name');
      return;
    }

    try {
      setSaving(true);
      setError('');

      const dashboardData = {
        name: dashboardName,
        description: dashboardDescription,
        layout_config: { columns: 12, rows: 8 },
        visuals: visuals.map((v, idx) => ({
          visual_type: v.type,
          config: { ...v.config, title: v.title },
          position: v.position,
          order: idx,
        })),
        project_id: activeProject.id,
      };

      if (isNewDashboard) {
        await dashboardsService.create(dashboardData);
      } else if (dashboard) {
        await dashboardsService.update(dashboard.id, dashboardData);
      }

      navigate('/dashboards');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save dashboard');
    } finally {
      setSaving(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Project</h3>
          <p className="text-gray-500">Please select a project first</p>
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

  const selectedVisualData = visuals.find((v) => v.id === selectedVisual);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboards')}
            className="text-gray-500 hover:text-gray-700"
          >
            ← Back
          </button>
          <input
            type="text"
            value={dashboardName}
            onChange={(e) => setDashboardName(e.target.value)}
            className="text-xl font-bold text-gray-900 border-none focus:ring-0 focus:outline-none bg-transparent"
            placeholder="Dashboard Name"
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddPanel(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <Plus className="w-5 h-5" />
            Add Visual
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Save className="w-5 h-5" />
            )}
            Save Dashboard
          </button>
        </div>
      </div>

      {error && (
        <div className="m-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Canvas */}
        <div className="flex-1 overflow-auto p-6 bg-gray-100">
          <div
            className="relative bg-white rounded-xl border border-gray-200 min-h-[600px]"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(12, 1fr)',
              gridAutoRows: '60px',
              gap: '8px',
              padding: '8px',
            }}
          >
            {visuals.length === 0 ? (
              <div className="col-span-12 row-span-4 flex items-center justify-center">
                <div className="text-center">
                  <Move className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No visuals yet</p>
                  <button
                    onClick={() => setShowAddPanel(true)}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Add Your First Visual
                  </button>
                </div>
              </div>
            ) : (
              visuals.map((visual) => {
                const VisualIcon =
                  VISUAL_TYPES.find((v) => v.type === visual.type)?.icon || BarChart3;
                return (
                  <div
                    key={visual.id}
                    onClick={() => setSelectedVisual(visual.id)}
                    className={`relative rounded-lg border-2 transition-all cursor-pointer ${
                      selectedVisual === visual.id
                        ? 'border-primary-500 shadow-lg'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    style={{
                      gridColumn: `span ${visual.position.width}`,
                      gridRow: `span ${visual.position.height}`,
                    }}
                  >
                    {/* Visual Header */}
                    <div className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-t-lg border-b border-gray-200">
                      <div className="flex items-center gap-2">
                        <GripVertical className="w-4 h-4 text-gray-400 cursor-move" />
                        <VisualIcon className="w-4 h-4 text-gray-500" />
                        <span className="text-sm font-medium text-gray-700 truncate">
                          {visual.title}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedVisual(visual.id);
                          }}
                          className="p-1 hover:bg-gray-200 rounded"
                        >
                          <Settings className="w-4 h-4 text-gray-500" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteVisual(visual.id);
                          }}
                          className="p-1 hover:bg-red-100 rounded"
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </div>

                    {/* Visual Content Placeholder */}
                    <div className="flex-1 flex items-center justify-center p-4">
                      <div className="text-center">
                        <VisualIcon className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                        <p className="text-xs text-gray-400">
                          Configure this visual in the panel
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Properties Panel */}
        {selectedVisualData && (
          <div className="w-80 border-l border-gray-200 bg-white overflow-y-auto">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">Visual Properties</h3>
                <button
                  onClick={() => setSelectedVisual(null)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            <div className="p-4 space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={selectedVisualData.title}
                  onChange={(e) => {
                    setVisuals(
                      visuals.map((v) =>
                        v.id === selectedVisualData.id ? { ...v, title: e.target.value } : v
                      )
                    );
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Visual Type
                </label>
                <select
                  value={selectedVisualData.type}
                  onChange={(e) => {
                    setVisuals(
                      visuals.map((v) =>
                        v.id === selectedVisualData.id
                          ? { ...v, type: e.target.value as VisualType }
                          : v
                      )
                    );
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  {VISUAL_TYPES.map((vt) => (
                    <option key={vt.type} value={vt.type}>
                      {vt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Size */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Size
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-gray-500">Width</label>
                    <input
                      type="number"
                      value={selectedVisualData.position.width}
                      onChange={(e) =>
                        updateVisualPosition(selectedVisualData.id, {
                          width: parseInt(e.target.value) || 1,
                        })
                      }
                      min={1}
                      max={12}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">Height</label>
                    <input
                      type="number"
                      value={selectedVisualData.position.height}
                      onChange={(e) =>
                        updateVisualPosition(selectedVisualData.id, {
                          height: parseInt(e.target.value) || 1,
                        })
                      }
                      min={1}
                      max={8}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              </div>

              {/* Placeholder for visual-specific config */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">
                  Additional configuration options would appear here based on the visual type.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Visual Panel */}
      {showAddPanel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Add Visual</h3>
              <button
                onClick={() => setShowAddPanel(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {VISUAL_TYPES.map((vt) => (
                <button
                  key={vt.type}
                  onClick={() => addVisual(vt.type)}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
                >
                  <vt.icon className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                  <div className="text-sm font-medium text-gray-700">{vt.label}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

