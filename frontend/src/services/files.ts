import api from './api';
import type { UploadedFile } from '@/types';

export const filesService = {
  list: async (project_id: number) => {
    const { data } = await api.get<UploadedFile[]>(`/api/v1/files/project/${project_id}`);
    return data;
  },

  get: async (id: number) => {
    const { data } = await api.get<UploadedFile>(`/api/v1/files/${id}`);
    return data;
  },

  upload: async (project_id: number, file: File) => {
    const formData = new FormData();
    formData.append('project_id', project_id.toString());
    formData.append('file', file);

    const { data } = await api.post<UploadedFile>('/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  markProcessed: async (file_id: number, dataset_id: string) => {
    const formData = new FormData();
    formData.append('dataset_id', dataset_id);

    const { data } = await api.post<UploadedFile>(
      `/api/v1/files/${file_id}/mark-processed`,
      formData
    );
    return data;
  },
};


