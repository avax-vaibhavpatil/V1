import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { projectsService } from '@/services/projects';
import type { Project } from '@/types';

interface ProjectContextType {
  projects: Project[];
  activeProject: Project | null;
  setActiveProject: (project: Project | null) => void;
  createProject: (name: string, description?: string) => Promise<Project>;
  refreshProjects: () => Promise<void>;
  loading: boolean;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsService.list();
      setProjects(data);
      
      // Restore active project from localStorage
      const savedProjectId = localStorage.getItem('activeProjectId');
      if (savedProjectId) {
        const project = data.find(p => p.id === parseInt(savedProjectId));
        if (project) {
          setActiveProject(project);
        }
      }
    } catch (error: any) {
      console.error('Failed to load projects:', error);
      console.error('Error details:', error.response?.data || error.message);
      // Set empty array on error so UI shows empty state
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (name: string, description?: string) => {
    const project = await projectsService.create({ name, description });
    await refreshProjects();
    setActiveProject(project);
    localStorage.setItem('activeProjectId', project.id.toString());
    return project;
  };

  const handleSetActiveProject = (project: Project | null) => {
    setActiveProject(project);
    if (project) {
      localStorage.setItem('activeProjectId', project.id.toString());
    } else {
      localStorage.removeItem('activeProjectId');
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  return (
    <ProjectContext.Provider
      value={{
        projects,
        activeProject,
        setActiveProject: handleSetActiveProject,
        createProject,
        refreshProjects,
        loading,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};


