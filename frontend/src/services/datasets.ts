import api from './api';
import type { Dataset, SemanticDefinition } from '@/types';

export interface DatasetPreview {
  results: Record<string, unknown>[];
  row_count: number;
  source: 'file' | 'sql';
  file_path?: string;
  message?: string;
}

export const datasetsService = {
  list: async (project_id?: number, skip = 0, limit = 100) => {
    const { data } = await api.get<Dataset[]>('/api/v1/datasets', {
      params: { project_id, skip, limit },
    });
    return data;
  },

  get: async (id: string) => {
    const { data } = await api.get<Dataset>(`/api/v1/datasets/${id}`);
    return data;
  },

  getSemantic: async (datasetId: string) => {
    try {
      const { data } = await api.get<SemanticDefinition>(`/api/v1/datasets/${datasetId}/semantic`);
      return data;
    } catch {
      // Return null if semantic not found
      return null;
    }
  },

  preview: async (datasetId: string, limit = 100) => {
    const { data } = await api.get<DatasetPreview>(`/api/v1/datasets/${datasetId}/preview`, {
      params: { limit },
    });
    return data;
  },

  create: async (dataset: {
    id: string;
    name: string;
    table_name: string;
    grain: string;
    schema_name?: string;
    description?: string;
    project_id?: number;
    source_type?: 'sql' | 'uploaded_file';
    uploaded_file_id?: number;
  }) => {
    const { data } = await api.post<Dataset>('/api/v1/datasets', dataset);
    return data;
  },

  update: async (id: string, dataset: { name?: string; description?: string }) => {
    const { data } = await api.patch<Dataset>(`/api/v1/datasets/${id}`, dataset);
    return data;
  },

  delete: async (id: string) => {
    await api.delete(`/api/v1/datasets/${id}`);
  },
};


