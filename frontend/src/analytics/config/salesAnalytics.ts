/**
 * 📊 SALES ANALYTICS REPORT CONFIGURATION
 * 
 * Database: PostgreSQL (analytics-llm)
 * Table: public.sales_analytics
 * Records: ~424,000 sales transactions
 * 
 * Key Metrics: Sales Amount, Profit/Loss, Quantity, Metal Weight
 * Dimensions: Item Group, Customer State, Industry, Material, Brand
 */

import type { ReportConfig } from '../types';

export const salesAnalyticsConfig: ReportConfig = {
  
  // ============================================
  // SECTION 1: BASIC INFO
  // ============================================
  reportId: 'sales-analytics',
  title: 'Sales Analytics Dashboard',
  description: 'Comprehensive sales performance analysis by product category, region, and customer segments',
  
  // ============================================
  // SECTION 2: DEFAULT VALUES
  // ============================================
  defaults: {
    time: {
      fiscalYear: '2025-2026',
      period: 'January 2026',  // Matches database format
    },
    toggles: {
      aggregation: 'YTD',
      metricMode: 'VALUE',
    },
    segments: {
      itemGroup: 'ALL',
      material: 'ALL',
    },
  },
  
  // ============================================
  // SECTION 3: API ENDPOINTS
  // ============================================
  data: {
    endpoints: {
      meta: '/api/v1/reports/sales-analytics/meta',
      kpis: '/api/v1/reports/sales-analytics/kpis',
      table: '/api/v1/reports/sales-analytics/table',
      drilldown: '/api/v1/reports/sales-analytics/drilldown',
      export: '/api/v1/reports/sales-analytics/export',
    },
    // Database mapping for backend queries
    dbConfig: {
      tableName: 'sales_analytics',
      dateColumn: 'asondate',
      periodColumn: 'period',
      metrics: {
        actualSales: 'SUM(saleamt_ason)',
        profitLoss: 'SUM(profitloss_ason)',
        quantity: 'SUM(saleqty_ason)',
        metalWeight: 'SUM(metalweightsold_ason)',
        receivables: 'SUM(item_receivable)',
      },
      dimensions: {
        entity: 'groupheadname',
        entityCode: 'branchcode',
        itemGroup: 'itemgroup',
        customerState: 'customer_state',
        industry: 'industry',
        material: 'material',
        brand: 'brand',
        customerCategory: 'customer_category',
        customerType: 'customer_type',
        regionalHead: 'regionalheadname',
        salesPerson: 'handledbyname',
        customer: 'customername',
      },
    },
  },
  
  // ============================================
  // SECTION 4: FILTERS
  // ============================================
  filters: [
    // Tab filter - Item Group (Main Product Categories)
    {
      key: 'itemGroup',
      label: 'Product Category',
      type: 'single',
      ui: 'tabs',
      optionsSource: 'static',
      dbColumn: 'itemgroup',
      options: [
        { label: 'All Categories', value: 'ALL' },
        { label: 'Building Wires', value: 'CABLES : BUILDING WIRES' },
        { label: 'Building Wires C90', value: 'CABLES : BUILDING WIRES C90' },
        { label: 'LT Cables', value: 'CABLES : LT' },
        { label: 'Flexibles (LDC)', value: 'CABLES : LDC (FLEX ETC)' },
        { label: 'HT & EHV', value: 'CABLES : HT & EHV' },
        { label: 'Switches', value: 'SWITCHES (WD)' },
        { label: 'Fans', value: 'FANS' },
        { label: 'Light Fixtures', value: 'LIGHT FIXTURE' },
      ],
    },
    
    // Chips filter - Material Type
    {
      key: 'material',
      label: 'Material',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      dbColumn: 'material',
      options: [
        { label: 'All', value: 'ALL' },
        { label: 'Copper', value: 'Copper' },
        { label: 'Aluminium', value: 'Aluminium' },
      ],
    },
    
    // Chips filter - Brand
    {
      key: 'brand',
      label: 'Brand',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      dbColumn: 'brand',
      options: [
        { label: 'All Brands', value: 'ALL' },
        { label: 'Polycab', value: 'POLYCAB' },
        { label: 'Prima Polycab', value: 'PRIMA POLYCAB' },
        { label: 'Etira', value: 'ETIRA' },
        { label: 'Anchor', value: 'ANCHOR' },
        { label: 'Schneider', value: 'SCHNEIDER' },
        { label: 'Crompton', value: 'CROMPTON' },
        { label: 'Philips', value: 'PHILIPS' },
      ],
    },
    
    // Multi-select - Customer State/Region
    {
      key: 'customerState',
      label: 'State/Region',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'static',
      dbColumn: 'customer_state',
      searchable: true,
      placeholder: 'Select states...',
      options: [
        { label: 'Maharashtra', value: 'Maharashtra' },
        { label: 'Gujarat', value: 'Gujarat' },
        { label: 'Karnataka', value: 'Karnataka' },
        { label: 'Tamil Nadu', value: 'Tamil Nadu' },
        { label: 'Andhra Pradesh', value: 'Andhra Pradesh' },
        { label: 'Telangana', value: 'Telangana' },
        { label: 'Kerala', value: 'Kerala' },
        { label: 'West Bengal', value: 'West Bengal' },
        { label: 'Chhattisgarh', value: 'Chhattisgarh' },
        { label: 'Madhya Pradesh', value: 'Madhya Pradesh' },
        { label: 'Rajasthan', value: 'Rajasthan' },
        { label: 'Uttar Pradesh', value: 'Uttar Pradesh' },
        { label: 'Delhi', value: 'Delhi' },
        { label: 'Punjab', value: 'Punjab' },
        { label: 'Haryana', value: 'Haryana' },
        { label: 'Bihar', value: 'Bihar' },
        { label: 'Odisha', value: 'Odisha' },
        { label: 'Goa', value: 'Goa' },
      ],
    },
    
    // Multi-select - Industry/Customer Segment
    {
      key: 'industry',
      label: 'Industry Segment',
      type: 'multi',
      ui: 'multiselect',
      optionsSource: 'static',
      dbColumn: 'industry',
      searchable: true,
      placeholder: 'Select segments...',
      options: [
        { label: 'Dealer - Local', value: 'DEALER   LOCAL' },
        { label: 'Dealer - Retailer', value: 'DEALER   RETAILER' },
        { label: 'Dealer - Up Country', value: 'DEALER   UP COUNTRY' },
        { label: 'Contractor - Small & Medium', value: 'CONTRACTOR   SMALL AND MEDIUM' },
        { label: 'Contractor - Regional & National', value: 'CONTRACTOR   REGIONAL AND NATIONAL' },
        { label: 'Builder', value: 'BUILDER' },
        { label: 'Industries', value: 'INDUSTRIES' },
        { label: 'Institutions', value: 'INSTITUTIONS' },
        { label: 'OEM', value: 'O.E.M' },
        { label: 'Exports', value: 'EXPORTS' },
        { label: 'Panel Builder', value: 'PANEL BUILDER' },
        { label: 'Government', value: 'GOVT.ORGANISATION' },
        { label: 'Architects', value: 'ARCHITECTS' },
        { label: 'Consultants', value: 'CONSULTANTS' },
      ],
    },
    
    // Chips filter - Customer Category (A-G rating)
    {
      key: 'customerCategory',
      label: 'Customer Rating',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      dbColumn: 'customer_category',
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
    
    // Chips filter - Customer Type
    {
      key: 'customerType',
      label: 'Customer Type',
      type: 'single',
      ui: 'chips',
      optionsSource: 'static',
      dbColumn: 'customer_type',
      options: [
        { label: 'All', value: 'ALL' },
        { label: 'Regular', value: 'Regular' },
        { label: 'New', value: 'New' },
        { label: 'Review', value: 'Review' },
      ],
    },
    
    // Period selector
    {
      key: 'period',
      label: 'Period',
      type: 'single',
      ui: 'select',
      optionsSource: 'static',
      dbColumn: 'period',
      options: [
        { label: 'January 2026', value: 'January 2026' },
        { label: 'December 2025', value: 'December 2025' },
        { label: 'November 2025', value: 'November 2025' },
        { label: 'October 2025', value: 'October 2025' },
        { label: 'September 2025', value: 'September 2025' },
        { label: 'August 2025', value: 'August 2025' },
        { label: 'July 2025', value: 'July 2025' },
        { label: 'June 2025', value: 'June 2025' },
        { label: 'May 2025', value: 'May 2025' },
        { label: 'April 2025', value: 'April 2025' },
      ],
    },
  ],
  
  // ============================================
  // SECTION 5: KPI CARDS - TOP ROW METRICS
  // ============================================
  kpis: {
    cards: [
      // KPI 1: Building Wires
      {
        id: 'buildingWires',
        title: 'Building Wires',
        primaryMetric: 'actualSales',
        secondaryMetric: 'profitLoss',
        shareMetric: 'contributionPct',
        trendMetric: 'marginPct',
        onClick: {
          type: 'highlight',
          groupKey: 'buildingWires',
        },
        tooltip: 'Building Wires sales including standard and C90 variants',
        dbFilter: "itemgroup LIKE 'CABLES : BUILDING WIRES%'",
      },
      
      // KPI 2: LT Cables
      {
        id: 'ltCables',
        title: 'LT Cables',
        primaryMetric: 'actualSales',
        secondaryMetric: 'profitLoss',
        shareMetric: 'contributionPct',
        trendMetric: 'marginPct',
        onClick: {
          type: 'highlight',
          groupKey: 'ltCables',
        },
        tooltip: 'Low Tension cables for power distribution',
        dbFilter: "itemgroup = 'CABLES : LT'",
      },
      
      // KPI 3: Flexibles (LDC)
      {
        id: 'flexibles',
        title: 'Flexibles (LDC)',
        primaryMetric: 'actualSales',
        secondaryMetric: 'profitLoss',
        shareMetric: 'contributionPct',
        trendMetric: 'marginPct',
        onClick: {
          type: 'highlight',
          groupKey: 'flexibles',
        },
        tooltip: 'Flexible cables and wires including single core and multi-core',
        dbFilter: "itemgroup = 'CABLES : LDC (FLEX ETC)'",
      },
      
      // KPI 4: HT & EHV
      {
        id: 'htEhv',
        title: 'HT & EHV',
        primaryMetric: 'actualSales',
        secondaryMetric: 'profitLoss',
        shareMetric: 'contributionPct',
        trendMetric: 'marginPct',
        onClick: {
          type: 'highlight',
          groupKey: 'htEhv',
        },
        tooltip: 'High Tension and Extra High Voltage cables',
        dbFilter: "itemgroup = 'CABLES : HT & EHV'",
      },
      
      // KPI 5: Total/Overall
      {
        id: 'overall',
        title: 'Total Sales',
        primaryMetric: 'actualSales',
        secondaryMetric: 'profitLoss',
        shareMetric: null,
        trendMetric: 'marginPct',
        onClick: {
          type: 'highlight',
          groupKey: 'overall',
        },
        tooltip: 'Total sales across all product categories',
        highlight: true,
      },
    ],
  },
  
  // ============================================
  // SECTION 6: TABLE CONFIGURATION
  // ============================================
  table: {
    // Entity column - Group Head
    entityColumn: {
      key: 'groupheadname',
      label: 'Group Head',
      pinned: true,
      secondaryKey: 'regionalheadname',
      secondaryLabel: 'Regional Head',
      dbColumn: 'groupheadname',
    },
    
    // Alternative view modes for entity
    entityViewModes: [
      { key: 'groupheadname', label: 'By Group Head' },
      { key: 'regionalheadname', label: 'By Regional Head' },
      { key: 'customer_state', label: 'By State' },
      { key: 'industry', label: 'By Industry' },
      { key: 'customername', label: 'By Customer' },
      { key: 'branchname', label: 'By Branch' },
    ],
    
    // Data columns grouped by product category
    columnGroups: [
      // Building Wires Group
      {
        groupLabel: 'Building Wires',
        groupKey: 'buildingWires',
        dbFilter: "itemgroup LIKE 'CABLES : BUILDING WIRES%'",
        columns: [
          { 
            key: 'buildingWires_actualSales',
            label: 'Sales',
            format: 'currencyCr',
            sortable: true,
            tooltip: 'Actual Sales Amount',
            dbExpression: 'SUM(saleamt_ason)',
          },
          { 
            key: 'buildingWires_profitLoss',
            label: 'P/L',
            format: 'currencyCr',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit/Loss',
            dbExpression: 'SUM(profitloss_ason)',
          },
          { 
            key: 'buildingWires_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Quantity Sold',
            dbExpression: 'SUM(saleqty_ason)',
          },
          { 
            key: 'buildingWires_margin',
            label: 'Margin%',
            format: 'percent',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit Margin %',
            dbExpression: 'CASE WHEN SUM(saleamt_ason) > 0 THEN SUM(profitloss_ason) * 100.0 / SUM(saleamt_ason) ELSE 0 END',
          },
        ],
      },
      
      // LT Cables Group
      {
        groupLabel: 'LT Cables',
        groupKey: 'ltCables',
        dbFilter: "itemgroup = 'CABLES : LT'",
        columns: [
          { 
            key: 'ltCables_actualSales',
            label: 'Sales',
            format: 'currencyCr',
            sortable: true,
            tooltip: 'Actual Sales Amount',
            dbExpression: 'SUM(saleamt_ason)',
          },
          { 
            key: 'ltCables_profitLoss',
            label: 'P/L',
            format: 'currencyCr',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit/Loss',
            dbExpression: 'SUM(profitloss_ason)',
          },
          { 
            key: 'ltCables_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Quantity Sold',
            dbExpression: 'SUM(saleqty_ason)',
          },
          { 
            key: 'ltCables_margin',
            label: 'Margin%',
            format: 'percent',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit Margin %',
            dbExpression: 'CASE WHEN SUM(saleamt_ason) > 0 THEN SUM(profitloss_ason) * 100.0 / SUM(saleamt_ason) ELSE 0 END',
          },
        ],
      },
      
      // Flexibles Group
      {
        groupLabel: 'Flexibles',
        groupKey: 'flexibles',
        dbFilter: "itemgroup = 'CABLES : LDC (FLEX ETC)'",
        columns: [
          { 
            key: 'flexibles_actualSales',
            label: 'Sales',
            format: 'currencyCr',
            sortable: true,
            tooltip: 'Actual Sales Amount',
            dbExpression: 'SUM(saleamt_ason)',
          },
          { 
            key: 'flexibles_profitLoss',
            label: 'P/L',
            format: 'currencyCr',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit/Loss',
            dbExpression: 'SUM(profitloss_ason)',
          },
          { 
            key: 'flexibles_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Quantity Sold',
            dbExpression: 'SUM(saleqty_ason)',
          },
          { 
            key: 'flexibles_margin',
            label: 'Margin%',
            format: 'percent',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit Margin %',
            dbExpression: 'CASE WHEN SUM(saleamt_ason) > 0 THEN SUM(profitloss_ason) * 100.0 / SUM(saleamt_ason) ELSE 0 END',
          },
        ],
      },
      
      // HT & EHV Group
      {
        groupLabel: 'HT & EHV',
        groupKey: 'htEhv',
        dbFilter: "itemgroup = 'CABLES : HT & EHV'",
        columns: [
          { 
            key: 'htEhv_actualSales',
            label: 'Sales',
            format: 'currencyCr',
            sortable: true,
            tooltip: 'Actual Sales Amount',
            dbExpression: 'SUM(saleamt_ason)',
          },
          { 
            key: 'htEhv_profitLoss',
            label: 'P/L',
            format: 'currencyCr',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit/Loss',
            dbExpression: 'SUM(profitloss_ason)',
          },
          { 
            key: 'htEhv_qty',
            label: 'Qty',
            format: 'integer',
            sortable: true,
            tooltip: 'Quantity Sold',
            dbExpression: 'SUM(saleqty_ason)',
          },
          { 
            key: 'htEhv_margin',
            label: 'Margin%',
            format: 'percent',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Profit Margin %',
            dbExpression: 'CASE WHEN SUM(saleamt_ason) > 0 THEN SUM(profitloss_ason) * 100.0 / SUM(saleamt_ason) ELSE 0 END',
          },
        ],
      },
      
      // Overall/Total Group
      {
        groupLabel: 'Overall',
        groupKey: 'overall',
        highlight: true,
        columns: [
          { 
            key: 'overall_actualSales',
            label: 'Total Sales',
            format: 'currencyCr',
            sortable: true,
            tooltip: 'Total Sales Amount',
            dbExpression: 'SUM(saleamt_ason)',
          },
          { 
            key: 'overall_profitLoss',
            label: 'Total P/L',
            format: 'currencyCr',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Total Profit/Loss',
            dbExpression: 'SUM(profitloss_ason)',
          },
          { 
            key: 'overall_metalWeight',
            label: 'Weight (MT)',
            format: 'decimal2',
            sortable: true,
            tooltip: 'Total Metal Weight Sold (MT)',
            dbExpression: 'SUM(metalweightsold_ason)',
          },
          { 
            key: 'overall_margin',
            label: 'Margin%',
            format: 'percent',
            conditional: 'posNeg',
            sortable: true,
            tooltip: 'Overall Profit Margin %',
            dbExpression: 'CASE WHEN SUM(saleamt_ason) > 0 THEN SUM(profitloss_ason) * 100.0 / SUM(saleamt_ason) ELSE 0 END',
          },
          { 
            key: 'overall_receivables',
            label: 'Receivables',
            format: 'currencyCr',
            sortable: true,
            tooltip: 'Outstanding Receivables',
            dbExpression: 'SUM(item_receivable)',
          },
        ],
      },
    ],
    
    // Default sorting
    defaultSort: {
      key: 'overall_actualSales',
      direction: 'desc',
    },
    pageSize: 50,
    virtualScroll: true,
    
    // Summary row configuration
    summaryRow: {
      enabled: true,
      label: 'Total',
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
      scale: 'Cr',
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
      'trendChart',
      'breakdownByCategory',
      'breakdownByProduct',
      'topCustomers',
      'materialMix',
    ],
    drilldownLevels: [
      { key: 'groupheadname', label: 'Group Head', nextLevel: 'regionalheadname' },
      { key: 'regionalheadname', label: 'Regional Head', nextLevel: 'handledbyname' },
      { key: 'handledbyname', label: 'Sales Person', nextLevel: 'customername' },
      { key: 'customername', label: 'Customer', nextLevel: null },
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
  
  // ============================================
  // SECTION 10: BACKEND SQL QUERY TEMPLATES
  // ============================================
  queryTemplates: {
    // Main table query template
    tableQuery: `
      SELECT 
        {{entityColumn}} as entity_name,
        {{secondaryColumn}} as entity_secondary,
        
        -- Building Wires
        SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleamt_ason ELSE 0 END) as "buildingWires_actualSales",
        SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN profitloss_ason ELSE 0 END) as "buildingWires_profitLoss",
        SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleqty_ason ELSE 0 END) as "buildingWires_qty",
        
        -- LT Cables
        SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleamt_ason ELSE 0 END) as "ltCables_actualSales",
        SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN profitloss_ason ELSE 0 END) as "ltCables_profitLoss",
        SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleqty_ason ELSE 0 END) as "ltCables_qty",
        
        -- Flexibles
        SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleamt_ason ELSE 0 END) as "flexibles_actualSales",
        SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN profitloss_ason ELSE 0 END) as "flexibles_profitLoss",
        SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleqty_ason ELSE 0 END) as "flexibles_qty",
        
        -- HT & EHV
        SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleamt_ason ELSE 0 END) as "htEhv_actualSales",
        SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN profitloss_ason ELSE 0 END) as "htEhv_profitLoss",
        SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleqty_ason ELSE 0 END) as "htEhv_qty",
        
        -- Overall
        SUM(saleamt_ason) as "overall_actualSales",
        SUM(profitloss_ason) as "overall_profitLoss",
        SUM(saleqty_ason) as "overall_qty",
        SUM(metalweightsold_ason) as "overall_metalWeight",
        SUM(item_receivable) as "overall_receivables"
        
      FROM sales_analytics
      WHERE 1=1
        {{periodFilter}}
        {{additionalFilters}}
      GROUP BY {{entityColumn}}, {{secondaryColumn}}
      HAVING SUM(saleamt_ason) > 0
      ORDER BY {{sortColumn}} {{sortDirection}}
      LIMIT {{pageSize}} OFFSET {{offset}}
    `,
    
    // KPI summary query template
    kpiQuery: `
      SELECT 
        SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN saleamt_ason ELSE 0 END) as "buildingWires_sales",
        SUM(CASE WHEN itemgroup LIKE 'CABLES : BUILDING WIRES%' THEN profitloss_ason ELSE 0 END) as "buildingWires_profit",
        
        SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN saleamt_ason ELSE 0 END) as "ltCables_sales",
        SUM(CASE WHEN itemgroup = 'CABLES : LT' THEN profitloss_ason ELSE 0 END) as "ltCables_profit",
        
        SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN saleamt_ason ELSE 0 END) as "flexibles_sales",
        SUM(CASE WHEN itemgroup = 'CABLES : LDC (FLEX ETC)' THEN profitloss_ason ELSE 0 END) as "flexibles_profit",
        
        SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN saleamt_ason ELSE 0 END) as "htEhv_sales",
        SUM(CASE WHEN itemgroup = 'CABLES : HT & EHV' THEN profitloss_ason ELSE 0 END) as "htEhv_profit",
        
        SUM(saleamt_ason) as total_sales,
        SUM(profitloss_ason) as total_profit,
        SUM(metalweightsold_ason) as total_weight
        
      FROM sales_analytics
      WHERE 1=1
        {{periodFilter}}
        {{additionalFilters}}
    `,
  },
};

export default salesAnalyticsConfig;



