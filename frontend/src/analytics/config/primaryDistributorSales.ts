/**
 * Primary Distributor Sales Dashboard Configuration
 * 
 * This is a sample report configuration demonstrating the config-driven
 * architecture. Adding a new report only requires creating a new config file.
 */

import type { ReportConfig } from '../types';

export const primaryDistributorSalesConfig: ReportConfig = {
  reportId: 'primary-distributor-sales',
  title: 'Primary Distributor Sales Dashboard',
  description: 'Performance analysis by category, distributor, and customer',
  
  defaults: {
    time: {
      fiscalYear: '2025-2026',
      period: 'DEC',
    },
    toggles: {
      aggregation: 'YTD',
      metricMode: 'VALUE',
    },
    segments: {
      channelType: 'CHANNEL',
    },
  },
  
  data: {
    endpoints: {
      meta: '/api/reports/primary-distributor-sales/meta',
      kpis: '/api/reports/primary-distributor-sales/kpis',
      table: '/api/reports/primary-distributor-sales/table',
      drilldown: '/api/reports/primary-distributor-sales/drilldown',
      export: '/api/reports/primary-distributor-sales/export',
    },
  },
  
  filters: [
    // Channel Type - Tab UI
    {
      key: 'channelType',
      label: 'Channel Type',
      type: 'single',
      ui: 'tabs',
      optionsSource: 'static',
      options: [
        { label: 'Channel', value: 'CHANNEL' },
        { label: 'Institutional', value: 'INSTITUTIONAL' },
      ],
    },
    // Entity Type - Tab UI
    {
      key: 'entityType',
      label: 'Entity Type',
      type: 'single',
      ui: 'tabs',
      optionsSource: 'static',
      options: [
        { label: 'Distributor', value: 'DISTRIBUTOR' },
        { label: 'Customer', value: 'CUSTOMER' },
      ],
    },
    // Zone - Chips UI
    {
      key: 'zone',
      label: 'Zone',
      type: 'single',
      ui: 'chips',
      optionsSource: 'api',
      endpoint: '/api/dimensions/zones',
      options: [
        { label: 'North', value: 'NORTH' },
        { label: 'South', value: 'SOUTH' },
        { label: 'East', value: 'EAST' },
        { label: 'West', value: 'WEST' },
        { label: 'Central', value: 'CENTRAL' },
      ],
    },
    // State - Multi-select
    {
      key: 'state',
      label: 'State',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'api',
      endpoint: '/api/dimensions/states?zone={zone}',
      dependsOn: ['zone'],
      searchable: true,
      placeholder: 'Select states...',
    },
    // Category
    {
      key: 'category',
      label: 'Category',
      type: 'single',
      ui: 'select',
      optionsSource: 'static',
      options: [
        { label: 'Project Wires', value: 'projectWires' },
        { label: 'Flexibles', value: 'flexibles' },
        { label: 'HDC', value: 'hdc' },
        { label: 'Dowells', value: 'dowells' },
        { label: 'FMEG', value: 'fmeg' },
        { label: 'Lumes', value: 'lumes' },
      ],
    },
  ],
  
  kpis: {
    cards: [
      {
        id: 'projectWires',
        title: 'Project Wires',
        primaryMetric: 'actualSales',
        secondaryMetric: 'targetSales',
        shareMetric: 'contributionPct',
        trendMetric: 'growthPct',
        onClick: {
          type: 'highlight',
          groupKey: 'projectWires',
        },
        tooltip: 'Cables and wires for project installations',
      },
      {
        id: 'flexibles',
        title: 'Flexibles',
        primaryMetric: 'actualSales',
        secondaryMetric: 'targetSales',
        shareMetric: 'contributionPct',
        trendMetric: 'growthPct',
        onClick: {
          type: 'highlight',
          groupKey: 'flexibles',
        },
        tooltip: 'Flexible wires and cables',
      },
      {
        id: 'hdc',
        title: 'HDC',
        primaryMetric: 'actualSales',
        secondaryMetric: 'targetSales',
        shareMetric: 'contributionPct',
        trendMetric: 'growthPct',
        onClick: {
          type: 'highlight',
          groupKey: 'hdc',
        },
        tooltip: 'Heavy Duty Cables',
      },
      {
        id: 'dowells',
        title: 'Dowells',
        primaryMetric: 'actualSales',
        secondaryMetric: 'targetSales',
        shareMetric: 'contributionPct',
        trendMetric: 'growthPct',
        onClick: {
          type: 'highlight',
          groupKey: 'dowells',
        },
        tooltip: 'Cable lugs and connectors',
      },
      {
        id: 'fmeg',
        title: 'FMEG',
        primaryMetric: 'actualSales',
        secondaryMetric: 'targetSales',
        shareMetric: 'contributionPct',
        trendMetric: 'growthPct',
        onClick: {
          type: 'highlight',
          groupKey: 'fmeg',
        },
        tooltip: 'Fans, Motors & Electrical Goods',
      },
      {
        id: 'lumes',
        title: 'Lumes',
        primaryMetric: 'actualSales',
        secondaryMetric: 'targetSales',
        shareMetric: 'contributionPct',
        trendMetric: 'growthPct',
        onClick: {
          type: 'highlight',
          groupKey: 'lumes',
        },
        tooltip: 'Lighting products',
      },
    ],
  },
  
  table: {
    entityColumn: {
      key: 'entityName',
      label: 'Distributor/Customer',
      pinned: true,
      secondaryKey: 'entityCode',
      secondaryLabel: 'Code',
    },
    columnGroups: [
      {
        groupLabel: 'Project Wires',
        groupKey: 'projectWires',
        columns: [
          { key: 'projectWires_actualSales', label: 'Act', format: 'currencyCr', sortable: true, tooltip: 'Actual Sales' },
          { key: 'projectWires_growthPct', label: '%G', format: 'percent', conditional: 'posNeg', sortable: true, tooltip: 'Growth %' },
          { key: 'projectWires_achievementPct', label: '%Ach', format: 'percent', sortable: true, tooltip: 'Achievement %' },
        ],
      },
      {
        groupLabel: 'Flexibles',
        groupKey: 'flexibles',
        columns: [
          { key: 'flexibles_actualSales', label: 'Act', format: 'currencyCr', sortable: true },
          { key: 'flexibles_growthPct', label: '%G', format: 'percent', conditional: 'posNeg', sortable: true },
          { key: 'flexibles_achievementPct', label: '%Ach', format: 'percent', sortable: true },
        ],
      },
      {
        groupLabel: 'HDC',
        groupKey: 'hdc',
        columns: [
          { key: 'hdc_actualSales', label: 'Act', format: 'currencyCr', sortable: true },
          { key: 'hdc_growthPct', label: '%G', format: 'percent', conditional: 'posNeg', sortable: true },
          { key: 'hdc_achievementPct', label: '%Ach', format: 'percent', sortable: true },
        ],
      },
      {
        groupLabel: 'Dowells',
        groupKey: 'dowells',
        columns: [
          { key: 'dowells_actualSales', label: 'Act', format: 'currencyCr', sortable: true },
          { key: 'dowells_growthPct', label: '%G', format: 'percent', conditional: 'posNeg', sortable: true },
          { key: 'dowells_achievementPct', label: '%Ach', format: 'percent', sortable: true },
        ],
      },
      {
        groupLabel: 'FMEG',
        groupKey: 'fmeg',
        columns: [
          { key: 'fmeg_actualSales', label: 'Act', format: 'currencyCr', sortable: true },
          { key: 'fmeg_growthPct', label: '%G', format: 'percent', conditional: 'posNeg', sortable: true },
          { key: 'fmeg_achievementPct', label: '%Ach', format: 'percent', sortable: true },
        ],
      },
      {
        groupLabel: 'Lumes',
        groupKey: 'lumes',
        columns: [
          { key: 'lumes_actualSales', label: 'Act', format: 'currencyCr', sortable: true },
          { key: 'lumes_growthPct', label: '%G', format: 'percent', conditional: 'posNeg', sortable: true },
          { key: 'lumes_achievementPct', label: '%Ach', format: 'percent', sortable: true },
        ],
      },
      {
        groupLabel: 'Overall',
        groupKey: 'overall',
        columns: [
          { key: 'overall_actualSales', label: 'Total', format: 'currencyCr', sortable: true },
          { key: 'overall_growthPct', label: '%G', format: 'percent', conditional: 'posNeg', sortable: true },
        ],
      },
    ],
    defaultSort: {
      key: 'overall_actualSales',
      direction: 'desc',
    },
    pageSize: 50,
    virtualScroll: false,
  },
  
  formatRules: {
    conditionalStyles: {
      posNeg: {
        positive: { color: '#16a34a', icon: 'arrowUp' },
        negative: { color: '#dc2626', icon: 'arrowDown' },
        zero: { color: '#6b7280', icon: 'dash' },
      },
    },
    currency: {
      symbol: '₹',
      scale: 'Cr',
    },
  },
  
  drilldown: {
    enabled: true,
    widgets: ['entitySummary', 'trendChart', 'breakdownByCategory', 'breakdownByProduct'],
  },
  
  features: {
    export: true,
    drilldown: true,
    share: true,
    refresh: true,
  },
};

export default primaryDistributorSalesConfig;

