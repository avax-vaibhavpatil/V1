/**
 * Analytics Dashboard Page
 * 
 * Main page component for the analytics dashboard.
 * Loads report configuration based on route parameter.
 */

import { useParams, Navigate } from 'react-router-dom';
import { ReportShell } from '@/analytics/components';
import { getReportConfig, primaryDistributorSalesConfig } from '@/analytics/config';

export default function AnalyticsDashboardPage() {
  const { reportId } = useParams<{ reportId?: string }>();
  
  // If no reportId provided, use default
  const configId = reportId || 'primary-distributor-sales';
  const config = getReportConfig(configId);
  
  // If config not found, redirect to default
  if (!config) {
    return <Navigate to="/analytics/primary-distributor-sales" replace />;
  }
  
  return <ReportShell config={config} />;
}

/**
 * Default Analytics Page - Shows the primary distributor sales dashboard
 */
export function DefaultAnalyticsDashboard() {
  return <ReportShell config={primaryDistributorSalesConfig} />;
}

