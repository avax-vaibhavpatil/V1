import api from './api';
import type { DatabaseConnection } from '@/types';

export const databaseConnectionsService = {
  list: async (project_id: number) => {
    const { data } = await api.get<DatabaseConnection[]>(
      `/api/v1/database-connections/project/${project_id}`
    );
    return data;
  },

  get: async (id: number) => {
    const { data } = await api.get<DatabaseConnection>(`/api/v1/database-connections/${id}`);
    return data;
  },

  test: async (connection: {
    db_type: string;
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
  }) => {
    const { data } = await api.post('/api/v1/database-connections/test', connection);
    return data;
  },

  create: async (connection: {
    project_id: number;
    name: string;
    db_type: 'postgresql' | 'mysql';
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
    schema_name?: string;
    is_read_only?: boolean;
  }) => {
    const { data } = await api.post<DatabaseConnection>(
      '/api/v1/database-connections',
      connection
    );
    return data;
  },

  listDatasets: async (connection_id: number, schema_name?: string) => {
    const { data } = await api.get(`/api/v1/database-connections/${connection_id}/datasets`, {
      params: { schema_name },
    });
    return data;
  },
};


