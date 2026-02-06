import api from './api';
import type { QueryRequest, QueryResponse } from '@/types';

export const queryService = {
  execute: async (request: QueryRequest) => {
    const { data } = await api.post<QueryResponse>('/api/v1/query/execute', request);
    return data;
  },
};


