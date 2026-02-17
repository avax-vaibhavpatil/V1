/**
 * 📊 STOCK INVENTORY (GODOWN-WISE) REPORT CONFIGURATION
 * 
 * Database: stock_gw (PostgreSQL)
 * Purpose: Inventory aging analysis, stock health monitoring, slow-moving stock identification
 * 
 * Key Metrics: Stock Value by Age, Sales, Profit/Loss, Stock Levels
 * Dimensions: Branch, Godown, Item, Make, Main Group, Sub Group
 */

import type { ReportConfig } from '../types';

export const stockInventoryConfig: ReportConfig = {
  
  // ============================================
  // SECTION 1: BASIC INFO
  // ============================================
  reportId: 'stock-inventory',
  title: 'Stock Inventory Dashboard',
  description: 'Godown-wise inventory aging analysis, stock health, and slow-moving stock monitoring',
  
  // ============================================
  // SECTION 2: DEFAULT VALUES
  // ============================================
  defaults: {
    time: {
      fiscalYear: '2025-2026',
      period: 'OCT',
    },
    toggles: {
      aggregation: 'MTD',
      metricMode: 'VALUE',
    },
    segments: {
      stockCondition: 'ALL',
      agingBucket: 'ALL',
    },
  },
  
  // ============================================
  // SECTION 3: API ENDPOINTS
  // ============================================
  data: {
    endpoints: {
      meta: '/api/v1/reports/stock-inventory/meta',
      kpis: '/api/v1/reports/stock-inventory/kpis',
      table: '/api/v1/reports/stock-inventory/table',
      drilldown: '/api/v1/reports/stock-inventory/drilldown',
      export: '/api/v1/reports/stock-inventory/export',
    },
    dbConfig: {
      tableName: 'stock_gw',
      dateColumn: 'stgw_date',
      metrics: {
        // Aging Buckets
        stock0to3m: 'SUM(stgw_val0_3m)',
        stock3to6m: 'SUM(stgw_val3_6m)',
        stock6mto1y: 'SUM(stgw_val6m_1y)',
        stock1yto2y: 'SUM(stgw_val1y_2y)',
        stock2yto3y: 'SUM(stgw_val2y_3y)',
        stock3yto4y: 'SUM(stgw_val3y_4y)',
        stockAbove4y: 'SUM(stgw_valabv_4y)',
        stockAbove1y: 'SUM(stgw_valabv_1y)',
        // Stock Condition
        drumStock: 'SUM(stgw_drum_val)',
        goodStock: 'SUM(stgw_good_val)',
        cutStock: 'SUM(stgw_cut_val)',
        scrapStock: 'SUM(stgw_scrap_val)',
        smallStock: 'SUM(stgw_small_val)',
        // Sales & Profit
        saleValue: 'SUM(stgw_sale_value)',
        sale90Days: 'SUM(stgw_sale90)',
        totalSaleValue: 'SUM(stgw_totsale_value)',
        profitLoss: 'SUM(stgw_profit_loss)',
        totalProfitLoss: 'SUM(stgw_total_profit_loss)',
        // Stock Level
        stockLevelValue: 'SUM(stgw_stock_lvl_value)',
        stockLevelCost: 'SUM(stgw_stock_lvl_cost)',
      },
      dimensions: {
        branch: 'branch_name',
        branchCode: 'stgw_branch_code',
        godownCode: 'stgw_godown_code',
        itemCode: 'stgw_item_code',
        itemName: 'item_name',
        make: 'stgw_make',
        mainGroup: 'stgw_main_group',
        subGroup: 'stgw_sub_group',
        company: 'company_name',
        companyCode: 'stgw_company_code',
      },
    },
  },
  
  // ============================================
  // SECTION 4: FILTERS
  // ============================================
  filters: [
    // Tab filter - Stock Health View
    {
      key: 'stockView',
      label: 'Stock View',
      type: 'single',
      ui: 'tabs',
      optionsSource: 'static',
      options: [
        { label: 'All Stock', value: 'ALL' },
        { label: 'Aging Analysis', value: 'AGING' },
        { label: 'Stock Condition', value: 'CONDITION' },
        { label: 'Slow Moving', value: 'SLOW_MOVING' },
      ],
    },
    
    // Chips filter - Stock Condition
    {
      key: 'stockCondition',
      label: 'Stock Condition',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      options: [
        { label: 'All', value: 'ALL' },
        { label: 'Drum', value: 'DRUM' },
        { label: 'Good', value: 'GOOD' },
        { label: 'Cut', value: 'CUT' },
        { label: 'Scrap', value: 'SCRAP' },
        { label: 'Small', value: 'SMALL' },
      ],
    },
    
    // Chips filter - Aging Bucket
    {
      key: 'agingBucket',
      label: 'Stock Age',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      options: [
        { label: 'All', value: 'ALL' },
        { label: '0-3 Months', value: '0_3M' },
        { label: '3-6 Months', value: '3_6M' },
        { label: '6M-1 Year', value: '6M_1Y' },
        { label: '1-2 Years', value: '1Y_2Y' },
        { label: '2-3 Years', value: '2Y_3Y' },
        { label: '3-4 Years', value: '3Y_4Y' },
        { label: 'Above 4 Years', value: 'ABV_4Y' },
      ],
    },
    
    // Multi-select - Branch
    {
      key: 'branch',
      label: 'Branch',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'static',
      searchable: true,
      placeholder: 'Select branches...',
      options: [
        { label: 'Mumbai', value: 'Mumbai' },
        { label: 'Secunderabad', value: 'Secunderabad' },
        { label: 'Kolkatta', value: 'Kolkatta' },
        { label: 'Bangalore', value: 'Bangalore' },
        { label: 'Chennai', value: 'Chennai' },
        { label: 'Baroda', value: 'Baroda' },
        { label: 'Vijayawada', value: 'Vijayawada' },
        { label: 'Rajkot', value: 'Rajkot' },
        { label: 'Coimbatore', value: 'Coimbatore' },
        { label: 'Kolhapur', value: 'Kolhapur' },
        { label: 'Bengaluru', value: 'Bengaluru' },
      ],
    },
    
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
    
    // Chips filter - Make/Brand
    {
      key: 'make',
      label: 'Make',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      options: [
        { label: 'All', value: 'ALL' },
        { label: 'Polycab', value: 'POL' },
        { label: 'Schneider', value: 'SNI' },
        { label: 'Legrand', value: 'LEG' },
        { label: 'ABB/Havells', value: 'AC9' },
        { label: 'Others', value: 'OTH' },
      ],
    },
    
    // Chips filter - Inventory Category
    {
      key: 'inventoryCategory',
      label: 'Inventory Rating',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      options: [
        { label: 'All', value: 'ALL' },
        { label: 'A', value: 'A' },
        { label: 'B', value: 'B' },
        { label: 'C', value: 'C' },
        { label: 'D', value: 'D' },
        { label: 'E', value: 'E' },
        { label: 'F', value: 'F' },
        { label: 'G', value: 'G' },
      ],
    },
  ],
  
  // ============================================
  // SECTION 5: KPI CARDS - TOP ROW METRICS
  // ============================================
  kpis: {
    cards: [
      // KPI 1: Fresh Stock (0-3 Months)
      {
        id: 'freshStock',
        title: 'Fresh Stock (0-3M)',
        primaryMetric: 'stock0to3m',
        secondaryMetric: 'stock0to3mQty',
        shareMetric: 'freshStockPct',
        trendMetric: null,
        onClick: {
          type: 'highlight',
          groupKey: 'aging0to3m',
        },
        tooltip: 'Stock received in last 3 months - healthy inventory',
        color: '#16a34a',
      },
      
      // KPI 2: Aging Stock (3M-1Y)
      {
        id: 'agingStock',
        title: 'Aging Stock (3M-1Y)',
        primaryMetric: 'stock3mTo1y',
        secondaryMetric: 'stock3mTo1yQty',
        shareMetric: 'agingStockPct',
        trendMetric: null,
        onClick: {
          type: 'highlight',
          groupKey: 'aging3mTo1y',
        },
        tooltip: 'Stock aging between 3 months to 1 year - needs attention',
        color: '#f59e0b',
      },
      
      // KPI 3: Slow Moving (1Y-2Y)
      {
        id: 'slowMoving',
        title: 'Slow Moving (1-2Y)',
        primaryMetric: 'stock1yto2y',
        secondaryMetric: 'stock1yto2yQty',
        shareMetric: 'slowMovingPct',
        trendMetric: null,
        onClick: {
          type: 'highlight',
          groupKey: 'aging1yTo2y',
        },
        tooltip: 'Slow moving stock 1-2 years old - requires action',
        color: '#f97316',
      },
      
      // KPI 4: Dead Stock (Above 2Y)
      {
        id: 'deadStock',
        title: 'Dead Stock (>2Y)',
        primaryMetric: 'stockAbove2y',
        secondaryMetric: 'stockAbove2yQty',
        shareMetric: 'deadStockPct',
        trendMetric: null,
        onClick: {
          type: 'highlight',
          groupKey: 'agingAbove2y',
        },
        tooltip: 'Dead stock above 2 years - critical for liquidation',
        color: '#dc2626',
      },
      
      // KPI 5: Total Stock Value
      {
        id: 'totalStock',
        title: 'Total Stock',
        primaryMetric: 'totalStockValue',
        secondaryMetric: 'totalStockQty',
        shareMetric: null,
        trendMetric: 'stockTurnover',
        onClick: {
          type: 'highlight',
          groupKey: 'overall',
        },
        tooltip: 'Total inventory value across all godowns',
        highlight: true,
      },
    ],
  },
  
  // ============================================
  // SECTION 6: TABLE CONFIGURATION
  // ============================================
  table: {
    entityColumn: {
      key: 'branch_name',
      label: 'Branch',
      pinned: true,
      secondaryKey: 'stgw_godown_code',
      secondaryLabel: 'Godown',
      dbColumn: 'branch_name',
    },
    
    entityViewModes: [
      { key: 'branch_name', label: 'By Branch' },
      { key: 'stgw_godown_code', label: 'By Godown' },
      { key: 'company_name', label: 'By Company' },
      { key: 'stgw_make', label: 'By Make' },
      { key: 'stgw_main_group', label: 'By Main Group' },
      { key: 'item_name', label: 'By Item' },
    ],
    
    columnGroups: [
      // Fresh Stock (0-3 Months)
      {
        groupLabel: '0-3 Months',
        groupKey: 'aging0to3m',
        highlight: false,
        healthIndicator: 'good',
        columns: [
          {
            key: 'aging0to3m_value',
            label: 'Value',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Stock Value (0-3 Months)',
            dbExpression: 'SUM(stgw_val0_3m)',
          },
          {
            key: 'aging0to3m_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Stock Quantity (0-3 Months)',
            dbExpression: 'SUM(stgw_qty0_3m)',
          },
          {
            key: 'aging0to3m_pct',
            label: '%',
            format: 'percent',
            sortable: true,
            tooltip: '% of Total Stock',
          },
        ],
      },
      
      // Aging Stock (3-6 Months)
      {
        groupLabel: '3-6 Months',
        groupKey: 'aging3to6m',
        healthIndicator: 'warning',
        columns: [
          {
            key: 'aging3to6m_value',
            label: 'Value',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Stock Value (3-6 Months)',
            dbExpression: 'SUM(stgw_val3_6m)',
          },
          {
            key: 'aging3to6m_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Stock Quantity (3-6 Months)',
            dbExpression: 'SUM(stgw_qty3_6m)',
          },
        ],
      },
      
      // Aging Stock (6M-1Y)
      {
        groupLabel: '6M-1 Year',
        groupKey: 'aging6mTo1y',
        healthIndicator: 'warning',
        columns: [
          {
            key: 'aging6mTo1y_value',
            label: 'Value',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Stock Value (6 Months to 1 Year)',
            dbExpression: 'SUM(stgw_val6m_1y)',
          },
          {
            key: 'aging6mTo1y_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Stock Quantity (6M-1Y)',
            dbExpression: 'SUM(stgw_qty6m_1y)',
          },
        ],
      },
      
      // Slow Moving (1-2 Years)
      {
        groupLabel: '1-2 Years',
        groupKey: 'aging1yTo2y',
        healthIndicator: 'danger',
        columns: [
          {
            key: 'aging1yTo2y_value',
            label: 'Value',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Stock Value (1-2 Years)',
            dbExpression: 'SUM(stgw_val1y_2y)',
          },
          {
            key: 'aging1yTo2y_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Stock Quantity (1-2 Years)',
            dbExpression: 'SUM(stgw_qty1y_2y)',
          },
        ],
      },
      
      // Dead Stock (Above 2 Years)
      {
        groupLabel: '>2 Years',
        groupKey: 'agingAbove2y',
        healthIndicator: 'critical',
        columns: [
          {
            key: 'agingAbove2y_value',
            label: 'Value',
            format: 'currencyLakh',
            conditional: 'negativeHighlight',
            sortable: true,
            tooltip: 'Dead Stock Value (Above 2 Years)',
            dbExpression: 'SUM(COALESCE(stgw_val2y_3y,0) + COALESCE(stgw_val3y_4y,0) + COALESCE(stgw_valabv_4y,0))',
          },
          {
            key: 'agingAbove2y_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Dead Stock Quantity',
            dbExpression: 'SUM(COALESCE(stgw_qty2y_3y,0) + COALESCE(stgw_qty3y_4y,0) + COALESCE(stgw_qtyabv_4y,0))',
          },
        ],
      },
      
      // Stock Condition
      {
        groupLabel: 'Good Stock',
        groupKey: 'goodStock',
        columns: [
          {
            key: 'good_value',
            label: 'Value',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Good Condition Stock Value',
            dbExpression: 'SUM(stgw_good_val)',
          },
          {
            key: 'good_nos',
            label: 'Nos',
            format: 'integer',
            sortable: true,
            tooltip: 'Number of Good Stock Items',
            dbExpression: 'SUM(stgw_good_nos)',
          },
        ],
      },
      
      // Sales Performance
      {
        groupLabel: 'Sales',
        groupKey: 'sales',
        columns: [
          {
            key: 'sale_value',
            label: 'Sales',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Current Period Sales',
            dbExpression: 'SUM(stgw_sale_value)',
          },
          {
            key: 'sale_90days',
            label: '90D Sales',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Last 90 Days Sales',
            dbExpression: 'SUM(stgw_sale90)',
          },
          {
            key: 'profit_loss',
            label: 'P/L',
            format: 'currencyLakh',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit/Loss',
            dbExpression: 'SUM(stgw_profit_loss)',
          },
        ],
      },
      
      // Overall/Total
      {
        groupLabel: 'Total Stock',
        groupKey: 'overall',
        highlight: true,
        columns: [
          {
            key: 'total_stock_value',
            label: 'Value',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Total Stock Value',
            dbExpression: 'SUM(COALESCE(stgw_val0_3m,0) + COALESCE(stgw_val3_6m,0) + COALESCE(stgw_val6m_1y,0) + COALESCE(stgw_val1y_2y,0) + COALESCE(stgw_val2y_3y,0) + COALESCE(stgw_val3y_4y,0) + COALESCE(stgw_valabv_4y,0))',
          },
          {
            key: 'stock_level_value',
            label: 'Lvl Val',
            format: 'currencyLakh',
            sortable: true,
            tooltip: 'Stock Level Value',
            dbExpression: 'SUM(stgw_stock_lvl_value)',
          },
          {
            key: 'total_profit_loss',
            label: 'Tot P/L',
            format: 'currencyLakh',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Total Profit/Loss',
            dbExpression: 'SUM(stgw_total_profit_loss)',
          },
        ],
      },
    ],
    
    defaultSort: {
      key: 'total_stock_value',
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
      negativeHighlight: {
        positive: { color: '#dc2626', background: '#fef2f2' },
        negative: { color: '#16a34a' },
        zero: { color: '#6b7280' },
      },
      healthIndicator: {
        good: { color: '#16a34a', background: '#f0fdf4' },
        warning: { color: '#f59e0b', background: '#fffbeb' },
        danger: { color: '#f97316', background: '#fff7ed' },
        critical: { color: '#dc2626', background: '#fef2f2' },
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
      'agingBreakdown',
      'conditionBreakdown',
      'topSlowMovingItems',
      'salesVsStock',
      'stockTurnoverTrend',
    ],
    drilldownLevels: [
      { key: 'branch_name', label: 'Branch', nextLevel: 'stgw_godown_code' },
      { key: 'stgw_godown_code', label: 'Godown', nextLevel: 'stgw_main_group' },
      { key: 'stgw_main_group', label: 'Main Group', nextLevel: 'stgw_sub_group' },
      { key: 'stgw_sub_group', label: 'Sub Group', nextLevel: 'item_name' },
      { key: 'item_name', label: 'Item', nextLevel: null },
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
    agingHeatmap: true,
    stockHealthScore: true,
  },
  
  // ============================================
  // SECTION 10: BACKEND SQL QUERY TEMPLATES
  // ============================================
  queryTemplates: {
    tableQuery: `
      SELECT 
        {{entityColumn}} as entity,
        {{secondaryColumn}} as entity_secondary,
        
        -- Aging 0-3 Months
        SUM(COALESCE(stgw_val0_3m, 0)) as aging0to3m_value,
        SUM(COALESCE(stgw_qty0_3m, 0)) as aging0to3m_qty,
        
        -- Aging 3-6 Months
        SUM(COALESCE(stgw_val3_6m, 0)) as aging3to6m_value,
        SUM(COALESCE(stgw_qty3_6m, 0)) as aging3to6m_qty,
        
        -- Aging 6M-1Y
        SUM(COALESCE(stgw_val6m_1y, 0)) as aging6mTo1y_value,
        SUM(COALESCE(stgw_qty6m_1y, 0)) as aging6mTo1y_qty,
        
        -- Aging 1-2 Years
        SUM(COALESCE(stgw_val1y_2y, 0)) as aging1yTo2y_value,
        SUM(COALESCE(stgw_qty1y_2y, 0)) as aging1yTo2y_qty,
        
        -- Aging Above 2 Years (Dead Stock)
        SUM(COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + COALESCE(stgw_valabv_4y, 0)) as agingAbove2y_value,
        SUM(COALESCE(stgw_qty2y_3y, 0) + COALESCE(stgw_qty3y_4y, 0) + COALESCE(stgw_qtyabv_4y, 0)) as agingAbove2y_qty,
        
        -- Good Stock
        SUM(COALESCE(stgw_good_val, 0)) as good_value,
        SUM(COALESCE(stgw_good_nos, 0)) as good_nos,
        
        -- Sales
        SUM(COALESCE(stgw_sale_value, 0)) as sale_value,
        SUM(COALESCE(stgw_sale90, 0)) as sale_90days,
        SUM(COALESCE(stgw_profit_loss, 0)) as profit_loss,
        
        -- Total
        SUM(COALESCE(stgw_val0_3m, 0) + COALESCE(stgw_val3_6m, 0) + COALESCE(stgw_val6m_1y, 0) + 
            COALESCE(stgw_val1y_2y, 0) + COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + 
            COALESCE(stgw_valabv_4y, 0)) as total_stock_value,
        SUM(COALESCE(stgw_stock_lvl_value, 0)) as stock_level_value,
        SUM(COALESCE(stgw_total_profit_loss, 0)) as total_profit_loss
        
      FROM stock_gw
      WHERE 1=1
        {{dateFilter}}
        {{additionalFilters}}
      GROUP BY {{entityColumn}}, {{secondaryColumn}}
      ORDER BY {{sortColumn}} {{sortDirection}}
      LIMIT {{pageSize}} OFFSET {{offset}}
    `,
    
    kpiQuery: `
      SELECT 
        SUM(COALESCE(stgw_val0_3m, 0)) as stock0to3m,
        SUM(COALESCE(stgw_val3_6m, 0) + COALESCE(stgw_val6m_1y, 0)) as stock3mTo1y,
        SUM(COALESCE(stgw_val1y_2y, 0)) as stock1yto2y,
        SUM(COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + COALESCE(stgw_valabv_4y, 0)) as stockAbove2y,
        SUM(COALESCE(stgw_val0_3m, 0) + COALESCE(stgw_val3_6m, 0) + COALESCE(stgw_val6m_1y, 0) + 
            COALESCE(stgw_val1y_2y, 0) + COALESCE(stgw_val2y_3y, 0) + COALESCE(stgw_val3y_4y, 0) + 
            COALESCE(stgw_valabv_4y, 0)) as totalStockValue,
        SUM(COALESCE(stgw_good_val, 0)) as goodStockValue,
        SUM(COALESCE(stgw_scrap_val, 0)) as scrapStockValue,
        SUM(COALESCE(stgw_sale_value, 0)) as totalSales,
        SUM(COALESCE(stgw_total_profit_loss, 0)) as totalProfitLoss
      FROM stock_gw
      WHERE 1=1
        {{dateFilter}}
        {{additionalFilters}}
    `,
    
    slowMovingItemsQuery: `
      SELECT 
        item_name,
        stgw_item_code,
        branch_name,
        SUM(COALESCE(stgw_valabv_1y, 0)) as slow_stock_value,
        SUM(COALESCE(stgw_qtyabv_1y, 0)) as slow_stock_qty,
        SUM(COALESCE(stgw_sale90, 0)) as last_90_days_sales
      FROM stock_gw
      WHERE COALESCE(stgw_valabv_1y, 0) > 0
        {{dateFilter}}
        {{additionalFilters}}
      GROUP BY item_name, stgw_item_code, branch_name
      ORDER BY slow_stock_value DESC
      LIMIT 50
    `,
  },
};

export default stockInventoryConfig;

