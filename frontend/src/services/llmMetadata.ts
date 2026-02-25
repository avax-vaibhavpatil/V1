import api from './api';
import type { LLMMetadata, TokenStatistics } from '@/types';

export const llmMetadataService = {
  list: async (skip = 0, limit = 50, reportId?: string) => {
    const { data } = await api.get<LLMMetadata[]>('/api/v1/llm-metadata', {
      params: { skip, limit, report_id: reportId },
    });
    return data;
  },

  getStats: async (reportId?: string) => {
    const { data } = await api.get<TokenStatistics>('/api/v1/llm-metadata/stats', {
      params: { report_id: reportId },
    });
    return data;
  },
};

