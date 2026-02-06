import api from './api';
import type { CalculationValidation } from '@/types';

export const calculationsService = {
  validate: async (formula: string, available_fields: string[]) => {
    const { data } = await api.post<CalculationValidation>('/api/v1/calculations/validate', {
      formula,
      available_fields,
    });
    return data;
  },

  parse: async (formula: string) => {
    const { data } = await api.post('/api/v1/calculations/parse', { formula });
    return data;
  },

  checkDivisionByZero: async (formula: string) => {
    const { data } = await api.post('/api/v1/calculations/check-division-by-zero', {
      formula,
    });
    return data;
  },
};


