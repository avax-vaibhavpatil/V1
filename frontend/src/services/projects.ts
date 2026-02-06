import api from './api';
import type { Project } from '@/types';

export const projectsService = {
  list: async (skip = 0, limit = 100, user_id?: string) => {
    const { data } = await api.get<Project[]>('/api/v1/projects', {
      params: { skip, limit, user_id },
    });
    return data;
  },

  get: async (id: number) => {
    const { data } = await api.get<Project>(`/api/v1/projects/${id}`);
    return data;
  },

  create: async (project: { name: string; description?: string }) => {
    const { data } = await api.post<Project>('/api/v1/projects', project);
    return data;
  },

  update: async (id: number, project: { name?: string; description?: string }) => {
    const { data } = await api.patch<Project>(`/api/v1/projects/${id}`, project);
    return data;
  },

  delete: async (id: number) => {
    await api.delete(`/api/v1/projects/${id}`);
  },
};


