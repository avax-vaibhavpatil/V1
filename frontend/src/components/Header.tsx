import { useProject } from '@/context/ProjectContext';
import { FolderKanban } from 'lucide-react';

export default function Header() {
  const { activeProject } = useProject();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FolderKanban className="w-6 h-6 text-primary-600" />
          <h1 className="text-xl font-semibold text-gray-900">Analytics Studio</h1>
        </div>
        {activeProject && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Active Project:</span>
            <span className="text-sm font-medium text-gray-900">{activeProject.name}</span>
          </div>
        )}
      </div>
    </header>
  );
}


