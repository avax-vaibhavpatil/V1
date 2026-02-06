/**
 * Report Configurations - Barrel Export
 * 
 * All report configs are exported from here.
 * To add a new report, create a new config file and export it here.
 */

export { primaryDistributorSalesConfig } from './primaryDistributorSales';
export { salesAnalyticsConfig } from './salesAnalytics';

// Export a registry of all configs for dynamic loading
import { primaryDistributorSalesConfig } from './primaryDistributorSales';
import { salesAnalyticsConfig } from './salesAnalytics';
import type { ReportConfig } from '../types';

export const reportConfigs: Record<string, ReportConfig> = {
  'primary-distributor-sales': primaryDistributorSalesConfig,
  'sales-analytics': salesAnalyticsConfig,
};

export function getReportConfig(reportId: string): ReportConfig | undefined {
  return reportConfigs[reportId];
}
