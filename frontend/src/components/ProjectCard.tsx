import { Check } from 'lucide-react';
import type { Project } from '@/types';

interface ProjectCardProps {
  project: Project;
  isActive: boolean;
  onSelect: () => void;
}

export default function ProjectCard({ project, isActive, onSelect }: ProjectCardProps) {
  return (
    <div
      onClick={onSelect}
      className={`p-6 bg-white rounded-lg border-2 cursor-pointer transition-all ${
        isActive
          ? 'border-primary-500 shadow-md'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
        {isActive && (
          <div className="flex items-center gap-1 text-primary-600">
            <Check className="w-5 h-5" />
            <span className="text-sm font-medium">Active</span>
          </div>
        )}
      </div>
      {project.description && (
        <p className="text-sm text-gray-500 mb-4">{project.description}</p>
      )}
      <div className="text-xs text-gray-400">
        Created {new Date(project.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}


