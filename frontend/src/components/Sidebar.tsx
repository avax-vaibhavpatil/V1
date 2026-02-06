import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  FolderKanban,
  Upload,
  BarChart3,
  Calculator,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { useProject } from '@/context/ProjectContext';

export default function Sidebar() {
  const { activeProject } = useProject();

  const navSections = [
    {
      title: 'Workspace',
      items: [
        { path: '/projects', icon: FolderKanban, label: 'Projects' },
      ],
    },
    {
      title: 'Data',
      items: [
        { path: '/datasets', icon: Database, label: 'Datasets' },
        { path: '/upload', icon: Upload, label: 'Upload Data' },
      ],
    },
    {
      title: 'Analytics',
      items: [
        { path: '/visual-builder', icon: BarChart3, label: 'Visual Builder' },
        { path: '/calculations', icon: Calculator, label: 'Calculations' },
        { path: '/dashboards', icon: LayoutDashboard, label: 'Dashboards' },
      ],
    },
    {
      title: 'Reports',
      items: [
        { path: '/analytics/primary-distributor-sales', icon: TrendingUp, label: 'Distributor Sales (Demo)' },
        { path: '/analytics/sales-analytics', icon: BarChart3, label: 'Sales Analytics (Live)' },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <nav className="flex-1 p-4 overflow-y-auto">
        {navSections.map((section) => (
          <div key={section.title} className="mb-6">
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">
              {section.title}
            </div>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                          isActive
                            ? 'bg-primary-50 text-primary-700 font-medium'
                            : 'text-gray-700 hover:bg-gray-50'
                        }`
                      }
                    >
                      <Icon className="w-5 h-5" />
                      <span className="flex-1">{item.label}</span>
                      <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100" />
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Active Project */}
      {activeProject && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-500 mb-1">Active Project</div>
          <div className="text-sm font-semibold text-gray-900 truncate">
            {activeProject.name}
          </div>
          {activeProject.description && (
            <div className="text-xs text-gray-500 truncate mt-0.5">
              {activeProject.description}
            </div>
          )}
        </div>
      )}

      {/* Quick Actions */}
      <div className="p-4 border-t border-gray-200">
        <NavLink
          to="/dashboards/new"
          className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
        >
          <LayoutDashboard className="w-4 h-4" />
          New Dashboard
        </NavLink>
      </div>
    </aside>
  );
}
