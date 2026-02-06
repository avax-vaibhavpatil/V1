/**
 * Mock Data Generator for Analytics Dashboard
 * 
 * Generates 1000+ rows of realistic sales data for:
 * - Distributors and Customers
 * - Multiple zones, states, regions
 * - Product categories: Project Wires, Flexibles, HDC, Dowells, FMEG, Lumes
 * - Metrics: Actual Sales, Target Sales, Growth %, Contribution %
 */

import type { TableRow, TrendDataPoint, BreakdownItem } from '../types';

// ============================================
// Static Data - Zones, States, Cities
// ============================================

export const ZONES = [
  { value: 'NORTH', label: 'North' },
  { value: 'SOUTH', label: 'South' },
  { value: 'EAST', label: 'East' },
  { value: 'WEST', label: 'West' },
  { value: 'CENTRAL', label: 'Central' },
];

export const STATES_BY_ZONE: Record<string, { value: string; label: string }[]> = {
  NORTH: [
    { value: 'DL', label: 'Delhi' },
    { value: 'HR', label: 'Haryana' },
    { value: 'PB', label: 'Punjab' },
    { value: 'UP', label: 'Uttar Pradesh' },
    { value: 'UK', label: 'Uttarakhand' },
    { value: 'HP', label: 'Himachal Pradesh' },
    { value: 'JK', label: 'Jammu & Kashmir' },
  ],
  SOUTH: [
    { value: 'KA', label: 'Karnataka' },
    { value: 'TN', label: 'Tamil Nadu' },
    { value: 'KL', label: 'Kerala' },
    { value: 'AP', label: 'Andhra Pradesh' },
    { value: 'TS', label: 'Telangana' },
  ],
  EAST: [
    { value: 'WB', label: 'West Bengal' },
    { value: 'OR', label: 'Odisha' },
    { value: 'JH', label: 'Jharkhand' },
    { value: 'BR', label: 'Bihar' },
    { value: 'AS', label: 'Assam' },
  ],
  WEST: [
    { value: 'MH', label: 'Maharashtra' },
    { value: 'GJ', label: 'Gujarat' },
    { value: 'RJ', label: 'Rajasthan' },
    { value: 'GA', label: 'Goa' },
  ],
  CENTRAL: [
    { value: 'MP', label: 'Madhya Pradesh' },
    { value: 'CG', label: 'Chhattisgarh' },
  ],
};

export const ALL_STATES = Object.values(STATES_BY_ZONE).flat();

// ============================================
// Product Categories
// ============================================

export const CATEGORIES = [
  { key: 'projectWires', label: 'Project Wires', shortLabel: 'PW' },
  { key: 'flexibles', label: 'Flexibles', shortLabel: 'FLX' },
  { key: 'hdc', label: 'HDC', shortLabel: 'HDC' },
  { key: 'dowells', label: 'Dowells', shortLabel: 'DWL' },
  { key: 'fmeg', label: 'FMEG', shortLabel: 'FMEG' },
  { key: 'lumes', label: 'Lumes', shortLabel: 'LUM' },
];

// ============================================
// Distributor/Customer Names
// ============================================

const DISTRIBUTOR_PREFIXES = [
  'MULTICAB', 'UNITED', 'PREMIER', 'GLOBAL', 'NATIONAL', 'ROYAL', 'SUPREME',
  'EXCEL', 'MEGA', 'STAR', 'GOLDEN', 'SILVER', 'DIAMOND', 'PLATINUM', 'ELITE',
  'PRIME', 'APEX', 'VERTEX', 'ZENITH', 'PINNACLE', 'SUMMIT', 'CREST', 'PEAK',
  'HORIZON', 'SUNRISE', 'SUNSET', 'EASTERN', 'WESTERN', 'NORTHERN', 'SOUTHERN',
  'CENTRAL', 'METRO', 'CITY', 'URBAN', 'RURAL', 'DISTRICT', 'REGIONAL',
];

const DISTRIBUTOR_SUFFIXES = [
  'CORPORATION', 'ENTERPRISES', 'TRADERS', 'DISTRIBUTORS', 'AGENCIES',
  'MARKETING', 'SOLUTIONS', 'SERVICES', 'INDUSTRIES', 'SYSTEMS',
  'ELECTRICAL', 'ELECTRONICS', 'WIRES', 'CABLES', 'POWER',
  'SALES', 'SUPPLIES', 'WHOLESALE', 'RETAIL', 'NETWORK',
];

const CUSTOMER_FIRST_NAMES = [
  'PRABHAT', 'RAJESH', 'SUNIL', 'ANIL', 'VIJAY', 'SANJAY', 'MANOJ', 'RAKESH',
  'DINESH', 'RAMESH', 'SURESH', 'MAHESH', 'NARESH', 'GANESH', 'UMESH',
  'AMIT', 'SUMIT', 'ROHIT', 'MOHIT', 'ANKIT', 'VIKAS', 'DEEPAK', 'ASHOK',
  'MUKESH', 'LOKESH', 'HITESH', 'RITESH', 'NITESH', 'PARESH', 'JITESH',
];

const CUSTOMER_LAST_NAMES = [
  'KUMAR', 'SHARMA', 'SINGH', 'VERMA', 'GUPTA', 'JAIN', 'AGARWAL', 'BANSAL',
  'MITTAL', 'GOEL', 'KHANNA', 'KAPOOR', 'MALHOTRA', 'CHOPRA', 'MEHTA',
  'SHAH', 'PATEL', 'DESAI', 'MODI', 'GANDHI', 'REDDY', 'RAO', 'NAIDU',
  'IYER', 'NAIR', 'MENON', 'PILLAI', 'DAS', 'SEN', 'BOSE', 'MUKHERJEE',
];

// ============================================
// Helper Functions
// ============================================

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomFloat(min: number, max: number, decimals: number = 2): number {
  const value = Math.random() * (max - min) + min;
  return Number(value.toFixed(decimals));
}

function randomElement<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function generateDistributorName(): string {
  return `${randomElement(DISTRIBUTOR_PREFIXES)} ${randomElement(DISTRIBUTOR_SUFFIXES)}`;
}

function generateCustomerName(): string {
  return `${randomElement(CUSTOMER_FIRST_NAMES)} ${randomElement(CUSTOMER_LAST_NAMES)}`;
}

function generateEntityCode(type: 'distributor' | 'customer', index: number): string {
  const prefix = type === 'distributor' ? 'D' : 'C';
  return `${prefix}${String(index).padStart(5, '0')}`;
}

// ============================================
// Sales Data Generation
// ============================================

interface EntityData {
  entityId: string;
  entityName: string;
  entityCode: string;
  entityType: 'DISTRIBUTOR' | 'CUSTOMER';
  channelType: 'CHANNEL' | 'INSTITUTIONAL';
  zone: string;
  state: string;
  region: string;
}

function generateEntityBase(index: number, type: 'distributor' | 'customer'): EntityData {
  const zone = randomElement(ZONES).value;
  const statesInZone = STATES_BY_ZONE[zone];
  const state = randomElement(statesInZone).value;
  
  return {
    entityId: generateEntityCode(type, index),
    entityName: type === 'distributor' ? generateDistributorName() : generateCustomerName(),
    entityCode: generateEntityCode(type, index),
    entityType: type === 'distributor' ? 'DISTRIBUTOR' : 'CUSTOMER',
    channelType: Math.random() > 0.3 ? 'CHANNEL' : 'INSTITUTIONAL',
    zone,
    state,
    region: `${state}-${randomInt(1, 5)}`,
  };
}

function generateCategorySales(baseScale: number): Record<string, number> {
  const result: Record<string, number> = {};
  
  CATEGORIES.forEach(cat => {
    // Generate actual sales with variance
    const actualBase = baseScale * randomFloat(0.5, 2.0);
    const actual = randomFloat(actualBase * 0.1, actualBase * 1.5);
    
    // Generate target (some entities have no target)
    const hasTarget = Math.random() > 0.2;
    const target = hasTarget ? randomFloat(actual * 0.7, actual * 1.3) : 0;
    
    // Calculate growth (can be positive, negative, or zero)
    const growthChance = Math.random();
    let growth: number;
    if (growthChance < 0.15) {
      growth = 0; // 15% chance of zero growth
    } else if (growthChance < 0.35) {
      growth = randomFloat(-50, -1); // 20% chance of negative growth
    } else {
      growth = randomFloat(1, 200); // 65% chance of positive growth
    }
    
    // Achievement percentage
    const achievement = target > 0 ? (actual / target) * 100 : 0;
    
    result[`${cat.key}_actualSales`] = Number(actual.toFixed(2));
    result[`${cat.key}_targetSales`] = Number(target.toFixed(2));
    result[`${cat.key}_growthPct`] = Number(growth.toFixed(1));
    result[`${cat.key}_achievementPct`] = Number(achievement.toFixed(1));
  });
  
  return result;
}

function calculateOverallMetrics(row: Record<string, number | string>): Record<string, number> {
  let totalActual = 0;
  let totalTarget = 0;
  let weightedGrowth = 0;
  
  CATEGORIES.forEach(cat => {
    const actual = row[`${cat.key}_actualSales`] as number || 0;
    const target = row[`${cat.key}_targetSales`] as number || 0;
    const growth = row[`${cat.key}_growthPct`] as number || 0;
    
    totalActual += actual;
    totalTarget += target;
    weightedGrowth += actual * growth;
  });
  
  const avgGrowth = totalActual > 0 ? weightedGrowth / totalActual : 0;
  const overallAchievement = totalTarget > 0 ? (totalActual / totalTarget) * 100 : 0;
  
  return {
    overall_actualSales: Number(totalActual.toFixed(2)),
    overall_targetSales: Number(totalTarget.toFixed(2)),
    overall_growthPct: Number(avgGrowth.toFixed(1)),
    overall_achievementPct: Number(overallAchievement.toFixed(1)),
  };
}

// ============================================
// Main Data Generation Functions
// ============================================

export interface GeneratedData {
  rows: TableRow[];
  meta: {
    totalDistributors: number;
    totalCustomers: number;
    totalRows: number;
    generatedAt: string;
  };
}

export function generateMockData(count: number = 1200): GeneratedData {
  const rows: TableRow[] = [];
  const distributorCount = Math.floor(count * 0.6); // 60% distributors
  const customerCount = count - distributorCount; // 40% customers
  
  // Generate distributors
  for (let i = 1; i <= distributorCount; i++) {
    const entity = generateEntityBase(i, 'distributor');
    const baseScale = randomFloat(10, 500); // Distributors have higher sales
    const categorySales = generateCategorySales(baseScale);
    const overallMetrics = calculateOverallMetrics(categorySales);
    
    rows.push({
      ...entity,
      ...categorySales,
      ...overallMetrics,
    } as TableRow);
  }
  
  // Generate customers
  for (let i = 1; i <= customerCount; i++) {
    const entity = generateEntityBase(i, 'customer');
    const baseScale = randomFloat(1, 100); // Customers have lower sales
    const categorySales = generateCategorySales(baseScale);
    const overallMetrics = calculateOverallMetrics(categorySales);
    
    rows.push({
      ...entity,
      ...categorySales,
      ...overallMetrics,
    } as TableRow);
  }
  
  return {
    rows,
    meta: {
      totalDistributors: distributorCount,
      totalCustomers: customerCount,
      totalRows: count,
      generatedAt: new Date().toISOString(),
    },
  };
}

// ============================================
// KPI Aggregation Functions
// ============================================

export interface KpiAggregates {
  id: string;
  actualSales: number;
  targetSales: number;
  growthPct: number;
  contributionPct: number;
  previousPeriodSales?: number;
}

export function aggregateKpis(rows: TableRow[]): KpiAggregates[] {
  const categoryTotals: Record<string, { actual: number; target: number; growth: number }> = {};
  let grandTotalActual = 0;
  
  // Initialize totals for each category
  CATEGORIES.forEach(cat => {
    categoryTotals[cat.key] = { actual: 0, target: 0, growth: 0 };
  });
  
  // Aggregate values
  rows.forEach(row => {
    CATEGORIES.forEach(cat => {
      const actual = (row[`${cat.key}_actualSales`] as number) || 0;
      const target = (row[`${cat.key}_targetSales`] as number) || 0;
      const growth = (row[`${cat.key}_growthPct`] as number) || 0;
      
      categoryTotals[cat.key].actual += actual;
      categoryTotals[cat.key].target += target;
      categoryTotals[cat.key].growth += actual * growth; // Weighted
      grandTotalActual += actual;
    });
  });
  
  // Build KPI cards
  return CATEGORIES.map(cat => {
    const totals = categoryTotals[cat.key];
    const avgGrowth = totals.actual > 0 ? totals.growth / totals.actual : 0;
    const contribution = grandTotalActual > 0 ? (totals.actual / grandTotalActual) * 100 : 0;
    
    return {
      id: cat.key,
      actualSales: Number(totals.actual.toFixed(2)),
      targetSales: Number(totals.target.toFixed(2)),
      growthPct: Number(avgGrowth.toFixed(1)),
      contributionPct: Number(contribution.toFixed(1)),
      previousPeriodSales: Number((totals.actual / (1 + avgGrowth / 100)).toFixed(2)),
    };
  });
}

// ============================================
// Trend Data Generation
// ============================================

export function generateTrendData(entityId: string, months: number = 12): TrendDataPoint[] {
  const trend: TrendDataPoint[] = [];
  const fiscalMonths = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'];
  
  let baseValue = randomFloat(50, 200);
  let baseTarget = baseValue * randomFloat(0.9, 1.1);
  
  for (let i = 0; i < months; i++) {
    // Add some variance and seasonal pattern
    const seasonalFactor = 1 + Math.sin((i / 12) * Math.PI * 2) * 0.2;
    const randomFactor = randomFloat(0.8, 1.2);
    
    const value = baseValue * seasonalFactor * randomFactor;
    const target = baseTarget * seasonalFactor;
    
    trend.push({
      period: fiscalMonths[i % 12],
      value: Number(value.toFixed(2)),
      target: Number(target.toFixed(2)),
    });
    
    // Slight trend increase
    baseValue *= randomFloat(0.98, 1.05);
    baseTarget *= 1.01;
  }
  
  return trend;
}

// ============================================
// Breakdown Data Generation
// ============================================

export function generateBreakdownData(entityId: string): Record<string, BreakdownItem[]> {
  const breakdown: Record<string, BreakdownItem[]> = {};
  
  // By category
  const categoryBreakdown: BreakdownItem[] = CATEGORIES.map(cat => {
    const value = randomFloat(10, 500);
    return {
      name: cat.label,
      value: Number(value.toFixed(2)),
      percentage: 0, // Will calculate after
      growth: randomFloat(-30, 100),
    };
  });
  
  const categoryTotal = categoryBreakdown.reduce((sum, item) => sum + item.value, 0);
  categoryBreakdown.forEach(item => {
    item.percentage = Number(((item.value / categoryTotal) * 100).toFixed(1));
  });
  
  breakdown.byCategory = categoryBreakdown.sort((a, b) => b.value - a.value);
  
  // By product (top products within entity)
  const products = [
    'Wire 1.5mm', 'Wire 2.5mm', 'Wire 4mm', 'Wire 6mm',
    'Flexible 0.75mm', 'Flexible 1mm', 'Flexible 1.5mm',
    'MCB 16A', 'MCB 32A', 'MCB 63A',
    'LED Bulb 9W', 'LED Bulb 12W', 'LED Panel 15W',
  ];
  
  const productBreakdown: BreakdownItem[] = products.slice(0, 8).map(product => {
    const value = randomFloat(5, 100);
    return {
      name: product,
      value: Number(value.toFixed(2)),
      percentage: 0,
      growth: randomFloat(-20, 80),
    };
  });
  
  const productTotal = productBreakdown.reduce((sum, item) => sum + item.value, 0);
  productBreakdown.forEach(item => {
    item.percentage = Number(((item.value / productTotal) * 100).toFixed(1));
  });
  
  breakdown.byProduct = productBreakdown.sort((a, b) => b.value - a.value);
  
  return breakdown;
}

// ============================================
// Filter Options
// ============================================

export const FISCAL_YEARS = [
  { value: '2025-2026', label: 'FY 2025-26' },
  { value: '2024-2025', label: 'FY 2024-25' },
  { value: '2023-2024', label: 'FY 2023-24' },
];

export const PERIODS = [
  { value: 'APR', label: 'April' },
  { value: 'MAY', label: 'May' },
  { value: 'JUN', label: 'June' },
  { value: 'JUL', label: 'July' },
  { value: 'AUG', label: 'August' },
  { value: 'SEP', label: 'September' },
  { value: 'OCT', label: 'October' },
  { value: 'NOV', label: 'November' },
  { value: 'DEC', label: 'December' },
  { value: 'JAN', label: 'January' },
  { value: 'FEB', label: 'February' },
  { value: 'MAR', label: 'March' },
];

export const CHANNEL_TYPES = [
  { value: 'CHANNEL', label: 'Channel' },
  { value: 'INSTITUTIONAL', label: 'Institutional' },
];

export const ENTITY_TYPES = [
  { value: 'DISTRIBUTOR', label: 'Distributor' },
  { value: 'CUSTOMER', label: 'Customer' },
];

export const AGGREGATIONS = [
  { value: 'YTD', label: 'Year to Date' },
  { value: 'QTD', label: 'Quarter to Date' },
  { value: 'MTD', label: 'Month to Date' },
];

export const METRIC_MODES = [
  { value: 'VALUE', label: 'Value (₹)' },
  { value: 'VOLUME', label: 'Volume (Units)' },
  { value: 'UNITS', label: 'Units' },
];

// ============================================
// Pre-generated Dataset (Singleton)
// ============================================

let cachedData: GeneratedData | null = null;

export function getMockData(): GeneratedData {
  if (!cachedData) {
    cachedData = generateMockData(1200);
  }
  return cachedData;
}

export function resetMockData(): void {
  cachedData = null;
}

