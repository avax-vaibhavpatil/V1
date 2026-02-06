import api from './api';
import type { Dashboard } from '@/types';

export const dashboardsService = {
  list: async (project_id?: number, skip = 0, limit = 100) => {
    const { data } = await api.get<Dashboard[]>('/api/v1/dashboards', {
      params: { project_id, skip, limit },
    });
    return data;
  },

  get: async (id: number) => {
    const { data } = await api.get<Dashboard>(`/api/v1/dashboards/${id}`);
    return data;
  },

  create: async (dashboard: {
    name: string;
    description?: string;
    layout_config: any;
    visuals: any[];
    is_public?: boolean;
    project_id?: number;
    dataset_id?: string;
  }) => {
    const { data } = await api.post<Dashboard>('/api/v1/dashboards', dashboard);
    return data;
  },

  update: async (id: number, dashboard: {
    name?: string;
    description?: string;
    layout_config?: any;
    visuals?: any[];
  }) => {
    const { data } = await api.patch<Dashboard>(`/api/v1/dashboards/${id}`, dashboard);
    return data;
  },

  delete: async (id: number) => {
    await api.delete(`/api/v1/dashboards/${id}`);
  },
};


