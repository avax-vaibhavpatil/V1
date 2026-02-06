import api from './api';
import type { DependencyUsage } from '@/types';

export const dependencySafetyService = {
  checkDatasetUsage: async (dataset_id: string) => {
    const { data } = await api.get<DependencyUsage>(
      `/api/v1/dependency-safety/dataset/${dataset_id}/usage`
    );
    return data;
  },

  validateDatasetDeletion: async (dataset_id: string, force = false) => {
    const { data } = await api.post(
      `/api/v1/dependency-safety/dataset/${dataset_id}/validate-deletion`,
      null,
      { params: { force } }
    );
    return data;
  },

  checkSemanticImpact: async (dataset_id: string, new_semantic: any) => {
    const { data } = await api.post(
      `/api/v1/dependency-safety/dataset/${dataset_id}/semantic-impact`,
      { new_semantic }
    );
    return data;
  },

  checkCalculationDependencies: async (measure_id: number) => {
    const { data } = await api.get(
      `/api/v1/dependency-safety/calculation/${measure_id}/dependencies`
    );
    return data;
  },
};


