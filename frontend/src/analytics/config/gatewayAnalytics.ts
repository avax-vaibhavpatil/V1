/**
 * 📊 GATEWAY ANALYTICS REPORT CONFIGURATION
 * 
 * Database: new_db (PostgreSQL)
 * Table: public.gwanalytics
 * Records: ~155,824 customer records
 * 
 * Key Metrics: YTD Sales, LYTD Sales, Outstanding Amount, Profit/Loss, Last 90 Days Sales
 * Dimensions: Customer, Sales Person, Company, Industry
 */

import type { ReportConfig } from '../types';

export const gatewayAnalyticsConfig: ReportConfig = {
  
  // ============================================
  // SECTION 1: BASIC INFO
  // ============================================
  reportId: 'gateway-analytics',
  title: 'Gateway Analytics Dashboard',
  description: 'Customer sales performance, outstanding analysis, and salesperson tracking',
  
  // ============================================
  // SECTION 2: DEFAULT VALUES
  // ============================================
  defaults: {
    time: {
      fiscalYear: '2025-2026',
      period: 'OCT',
    },
    toggles: {
      aggregation: 'YTD',
      metricMode: 'VALUE',
    },
    segments: {
      company: 'ALL',
      industry: 'ALL',
    },
  },
  
  // ============================================
  // SECTION 3: API ENDPOINTS
  // ============================================
  data: {
    endpoints: {
      meta: '/api/v1/reports/gateway-analytics/meta',
      kpis: '/api/v1/reports/gateway-analytics/kpis',
      table: '/api/v1/reports/gateway-analytics/table',
      drilldown: '/api/v1/reports/gateway-analytics/drilldown',
      export: '/api/v1/reports/gateway-analytics/export',
    },
    dbConfig: {
      tableName: 'gwanalytics',
      dateColumn: 'gws_date',
      metrics: {
        // Sales Metrics
        ytdSales: 'SUM(gws_ytd_sales)',
        lytdSales: 'SUM(gws_lytd_sales)',
        last90Sales: 'SUM(gws_last90_sales)',
        yesterdaySale: 'SUM(gws_yesterday_sale)',
        cymtdSale: 'SUM(gws_cymtd_sale)',
        lymtdSale: 'SUM(gws_lymtd_sale)',
        // Outstanding
        osAmount: 'SUM(gws_os_amount)',
        osAbv180: 'SUM(gws_os_abv_180)',
        osAbv90: 'SUM(gws_os_abv_90)',
        dueOs: 'SUM(gws_due_os)',
        nonDueOs: 'SUM(gws_non_due_os)',
        // Profit/Loss
        profitLoss: 'SUM(gws_profit_loss)',
        lyProfitLoss: 'SUM(gws_ly_profit_loss)',
        // Pending
        pendingAoAmt: 'SUM(gws_pending_ao_amt)',
        pendingQuotAmt: 'SUM(gws_pending_quot_amt)',
        pendingCformAmt: 'SUM(gws_pending_cform_amt)',
        pendingRdbAmt: 'SUM(gws_pending_rdb_amt)',
        pendingGrbAmt: 'SUM(gws_pending_grb_amt)',
        // Budget
        ytdBudget: 'SUM(gws_ytd_budget)',
      },
      dimensions: {
        customer: 'cust_name',
        customerCode: 'gws_cust_code',
        salesPerson: 'handled_name',
        salesPersonCode: 'gws_handled_by',
        company: 'company_name',
        companyCode: 'gws_company_code',
        industry: 'gws_industry_code',
        partyFlag: 'gws_party_flg',
      },
    },
  },
  
  // ============================================
  // SECTION 4: FILTERS
  // ============================================
  filters: [
    // Multi-select - Company
    {
      key: 'company',
      label: 'Company',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'static',
      searchable: true,
      placeholder: 'Select companies...',
      options: [
        { label: 'Shree NM Electricals Ltd', value: 'Shree NM Electricals Ltd' },
        { label: 'DeltonControl & Switchgears LLP', value: 'DeltonControl & Switchgears LLP' },
        { label: 'Vraj Electricals LLP', value: 'Vraj Electricals LLP' },
        { label: 'TECHMECH NM SOLUTIONS LLP', value: 'TECHMECH NM SOLUTIONS LLP' },
        { label: 'TECHMECH ELECTRIFY LLP', value: 'TECHMECH ELECTRIFY LLP' },
        { label: 'Poojapower Control & Automation LLP', value: 'Poojapower Control & Automation LLP' },
      ],
    },
    
    // Multi-select - Sales Person
    {
      key: 'salesPerson',
      label: 'Sales Person',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'api',
      searchable: true,
      placeholder: 'Select sales persons...',
    },
    
    // Chips filter - Industry
    {
      key: 'industry',
      label: 'Industry',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      options: [
        { label: 'All', value: 'ALL' },
      ],
    },
  ],
  
  // ============================================
  // SECTION 5: KPI CARDS
  // ============================================
  kpis: {
    cards: [
      {
        id: 'ytdSales',
        title: 'YTD Sales',
        primaryMetric: 'ytdSales',
        secondaryMetric: null,
        shareMetric: null,
        trendMetric: 'ytdSalesGrowth',
        tooltip: 'Year to Date Sales',
        highlight: true,
      },
      {
        id: 'outstanding',
        title: 'Outstanding',
        primaryMetric: 'osAmount',
        secondaryMetric: 'osAbv180',
        shareMetric: null,
        trendMetric: null,
        tooltip: 'Total Outstanding Amount',
        color: '#f59e0b',
      },
      {
        id: 'profitLoss',
        title: 'Profit/Loss',
        primaryMetric: 'profitLoss',
        secondaryMetric: null,
        shareMetric: null,
        trendMetric: null,
        tooltip: 'Current Period Profit/Loss',
        conditional: 'posNeg',
      },
      {
        id: 'last90Sales',
        title: 'Last 90 Days',
        primaryMetric: 'last90Sales',
        secondaryMetric: null,
        shareMetric: null,
        trendMetric: null,
        tooltip: 'Sales in Last 90 Days',
      },
    ],
  },
  
  // ============================================
  // SECTION 6: TABLE CONFIGURATION
  // ============================================
  table: {
    entityColumn: {
      key: 'cust_name',
      label: 'Customer',
      pinned: true,
      secondaryKey: 'gws_cust_code',
      secondaryLabel: 'Code',
      dbColumn: 'cust_name',
    },
    
    entityViewModes: [
      { key: 'cust_name', label: 'By Customer' },
      { key: 'handled_name', label: 'By Sales Person' },
      { key: 'company_name', label: 'By Company' },
      { key: 'gws_industry_code', label: 'By Industry' },
    ],
    
    columnGroups: [
      {
        groupLabel: 'Sales',
        groupKey: 'sales',
        columns: [
          {
            key: 'ytd_sales',
            label: 'YTD Sales',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Year to Date Sales',
            dbExpression: 'SUM(gws_ytd_sales)',
          },
          {
            key: 'lytd_sales',
            label: 'LYTD Sales',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Last Year to Date Sales',
            dbExpression: 'SUM(gws_lytd_sales)',
          },
          {
            key: 'last90_sales',
            label: '90D Sales',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Last 90 Days Sales',
            dbExpression: 'SUM(gws_last90_sales)',
          },
          {
            key: 'profit_loss',
            label: 'P/L',
            format: 'currencyLakh',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit/Loss',
            dbExpression: 'SUM(gws_profit_loss)',
          },
        ],
      },
      {
        groupLabel: 'Outstanding',
        groupKey: 'outstanding',
        columns: [
          {
            key: 'os_amount',
            label: 'Total OS',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Total Outstanding Amount',
            dbExpression: 'SUM(gws_os_amount)',
          },
          {
            key: 'os_abv_180',
            label: 'OS >180D',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Outstanding Above 180 Days',
            dbExpression: 'SUM(gws_os_abv_180)',
          },
          {
            key: 'os_abv_90',
            label: 'OS >90D',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Outstanding Above 90 Days',
            dbExpression: 'SUM(gws_os_abv_90)',
          },
          {
            key: 'due_os',
            label: 'Due OS',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Due Outstanding',
            dbExpression: 'SUM(gws_due_os)',
          },
        ],
      },
      {
        groupLabel: 'Pending',
        groupKey: 'pending',
        columns: [
          {
            key: 'pending_ao_amt',
            label: 'AO Amount',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Pending AO Amount',
            dbExpression: 'SUM(gws_pending_ao_amt)',
          },
          {
            key: 'pending_quot_amt',
            label: 'Quote Amount',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Pending Quote Amount',
            dbExpression: 'SUM(gws_pending_quot_amt)',
          },
        ],
      },
    ],
    
    defaultSort: {
      key: 'ytd_sales',
      direction: 'desc',
    },
    pageSize: 50,
    virtualScroll: true,
    
    summaryRow: {
      enabled: true,
      label: 'Grand Total',
      position: 'top',
    },
  },
  
  // ============================================
  // SECTION 7: FORMATTING RULES
  // ============================================
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
      scale: 'Lakh',
      scaleFactors: {
        'Cr': 10000000,
        'Lakh': 100000,
        'K': 1000,
      },
    },
    number: {
      decimal2: { decimals: 2 },
      integer: { decimals: 0, thousandsSeparator: true },
      percent: { decimals: 1, suffix: '%' },
    },
  },
  
  // ============================================
  // SECTION 8: DRILLDOWN CONFIG
  // ============================================
  drilldown: {
    enabled: true,
    triggerColumn: 'entityColumn',
    widgets: [
      'entitySummary',
      'salesTrend',
      'outstandingBreakdown',
      'pendingDetails',
    ],
    drilldownLevels: [
      { key: 'cust_name', label: 'Customer', nextLevel: null },
    ],
  },
  
  // ============================================
  // SECTION 9: FEATURE FLAGS
  // ============================================
  features: {
    export: true,
    drilldown: true,
    share: true,
    refresh: true,
    print: true,
    columnToggle: true,
    viewModeSwitch: true,
  },
};

export default gatewayAnalyticsConfig;

