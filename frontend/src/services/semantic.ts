import api from './api';
import type { SemanticDefinition } from '@/types';

export const semanticService = {
  validate: async (schema: SemanticDefinition) => {
    const { data } = await api.post('/api/v1/semantic/validate', {
      schema_json: schema,
    });
    return data;
  },

  parse: async (schema: SemanticDefinition) => {
    const { data } = await api.post('/api/v1/semantic/parse', {
      schema_json: schema,
    });
    return data;
  },

  validateField: async (params: {
    schema: SemanticDefinition;
    field_name: string;
    field_type: 'dimension' | 'measure';
    aggregation?: string;
  }) => {
    const { data } = await api.post('/api/v1/semantic/validate-field', params);
    return data;
  },
};


