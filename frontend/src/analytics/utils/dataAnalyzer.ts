/**
 * Data Analyzer - AI-like Analysis Engine for Report Data
 * 
 * Parses natural language questions and generates intelligent responses
 * based on the current report data.
 */

import type { TableRow, KpiCardData } from '../types';
import { CATEGORIES } from '../data/mockDataGenerator';

// ============================================
// Types
// ============================================

export interface AnalysisContext {
  rows: TableRow[];
  kpis: KpiCardData[];
  filters: {
    zone?: string;
    state?: string[];
    channelType?: string;
    entityType?: string;
  };
  aggregation: string;
}

export interface AnalysisResult {
  answer: string;
  data?: Record<string, unknown>[];
  chartSuggestion?: 'bar' | 'pie' | 'line' | 'table';
  confidence: 'high' | 'medium' | 'low';
}

// ============================================
// Question Patterns
// ============================================

const PATTERNS = {
  topPerformers: /(?:top|best|highest|leading)\s*(\d+)?\s*(?:performer|distributor|customer|seller|entity|entities)?/i,
  bottomPerformers: /(?:bottom|worst|lowest|poor|underperform)\s*(\d+)?\s*(?:performer|distributor|customer|seller|entity|entities)?/i,
  totalSales: /(?:total|overall|sum|aggregate)\s*(?:sales|revenue|value)/i,
  categoryCompare: /(?:compare|vs|versus|between)\s+(\w+)\s+(?:and|vs|versus|&)\s+(\w+)/i,
  specificCategory: /(?:sales|revenue|performance|growth)\s*(?:for|of|in)?\s*(project\s*wires?|flexibles?|hdc|dowells?|fmeg|lumes?)/i,
  growthAnalysis: /(?:growth|growing|decline|declining|trend)/i,
  achievementAnalysis: /(?:achievement|target|goal|ach%|%ach)/i,
  zoneAnalysis: /(?:zone|region|area)\s*(?:wise|breakdown|analysis|performance)?/i,
  averageSales: /(?:average|avg|mean)\s*(?:sales|revenue|value)/i,
  countEntities: /(?:how many|count|number of|total)\s*(?:distributor|customer|entit)/i,
  contributionAnalysis: /(?:contribution|share|%|percent)/i,
  maxMin: /(?:maximum|minimum|max|min|highest|lowest)\s*(?:sales|revenue|growth|achievement)/i,
  summary: /(?:summary|summarize|overview|insight|report)/i,
  help: /(?:help|what can you|how to|capabilities)/i,
};

// ============================================
// Helper Functions
// ============================================

function getCategoryKey(input: string): string | null {
  const normalized = input.toLowerCase().replace(/\s+/g, '');
  const mapping: Record<string, string> = {
    'projectwires': 'projectWires',
    'projectwire': 'projectWires',
    'pw': 'projectWires',
    'flexibles': 'flexibles',
    'flexible': 'flexibles',
    'flx': 'flexibles',
    'hdc': 'hdc',
    'dowells': 'dowells',
    'dowell': 'dowells',
    'dwl': 'dowells',
    'fmeg': 'fmeg',
    'lumes': 'lumes',
    'lume': 'lumes',
    'lum': 'lumes',
  };
  return mapping[normalized] || null;
}

function getCategoryLabel(key: string): string {
  const cat = CATEGORIES.find(c => c.key === key);
  return cat?.label || key;
}

function formatCurrency(value: number): string {
  if (value >= 100) return `₹${value.toFixed(0)} Cr`;
  if (value >= 10) return `₹${value.toFixed(1)} Cr`;
  return `₹${value.toFixed(2)} Cr`;
}

function formatPercent(value: number): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

function getTopN<T>(arr: T[], key: keyof T, n: number, ascending = false): T[] {
  return [...arr]
    .sort((a, b) => {
      const aVal = Number(a[key]) || 0;
      const bVal = Number(b[key]) || 0;
      return ascending ? aVal - bVal : bVal - aVal;
    })
    .slice(0, n);
}

function calculateStats(values: number[]): { sum: number; avg: number; min: number; max: number; count: number } {
  const filtered = values.filter(v => !isNaN(v) && v !== null && v !== undefined);
  if (filtered.length === 0) return { sum: 0, avg: 0, min: 0, max: 0, count: 0 };
  
  const sum = filtered.reduce((a, b) => a + b, 0);
  return {
    sum,
    avg: sum / filtered.length,
    min: Math.min(...filtered),
    max: Math.max(...filtered),
    count: filtered.length,
  };
}

// ============================================
// Analysis Functions
// ============================================

function analyzeTopPerformers(ctx: AnalysisContext, count: number = 5): AnalysisResult {
  const top = getTopN(ctx.rows, 'overall_actualSales', count);
  
  const listItems = top.map((row, i) => 
    `${i + 1}. **${row.entityName}** - ${formatCurrency(row.overall_actualSales as number)} (Growth: ${formatPercent(row.overall_growthPct as number)})`
  ).join('\n');
  
  return {
    answer: `📊 **Top ${count} Performers by Total Sales:**\n\n${listItems}\n\n💡 These entities contribute significantly to the overall sales volume.`,
    data: top.map(r => ({ name: r.entityName, sales: r.overall_actualSales, growth: r.overall_growthPct })),
    chartSuggestion: 'bar',
    confidence: 'high',
  };
}

function analyzeBottomPerformers(ctx: AnalysisContext, count: number = 5): AnalysisResult {
  const bottom = getTopN(ctx.rows, 'overall_actualSales', count, true);
  
  const listItems = bottom.map((row, i) => 
    `${i + 1}. **${row.entityName}** - ${formatCurrency(row.overall_actualSales as number)} (Growth: ${formatPercent(row.overall_growthPct as number)})`
  ).join('\n');
  
  return {
    answer: `📉 **Bottom ${count} Performers by Total Sales:**\n\n${listItems}\n\n⚠️ These entities may need attention or support to improve performance.`,
    data: bottom.map(r => ({ name: r.entityName, sales: r.overall_actualSales, growth: r.overall_growthPct })),
    chartSuggestion: 'bar',
    confidence: 'high',
  };
}

function analyzeTotalSales(ctx: AnalysisContext): AnalysisResult {
  const totals = CATEGORIES.map(cat => {
    const values = ctx.rows.map(r => (r[`${cat.key}_actualSales`] as number) || 0);
    const stats = calculateStats(values);
    return { category: cat.label, total: stats.sum };
  });
  
  const grandTotal = totals.reduce((sum, t) => sum + t.total, 0);
  
  const breakdown = totals
    .sort((a, b) => b.total - a.total)
    .map(t => `• **${t.category}**: ${formatCurrency(t.total)} (${((t.total / grandTotal) * 100).toFixed(1)}%)`)
    .join('\n');
  
  return {
    answer: `💰 **Total Sales Analysis:**\n\n**Grand Total: ${formatCurrency(grandTotal)}**\n\n**Category Breakdown:**\n${breakdown}\n\n📈 This data is based on ${ctx.rows.length} entities in the current view.`,
    data: totals,
    chartSuggestion: 'pie',
    confidence: 'high',
  };
}

function analyzeCategory(ctx: AnalysisContext, categoryKey: string): AnalysisResult {
  const label = getCategoryLabel(categoryKey);
  const actualKey = `${categoryKey}_actualSales`;
  const growthKey = `${categoryKey}_growthPct`;
  const achieveKey = `${categoryKey}_achievementPct`;
  
  const values = ctx.rows.map(r => (r[actualKey] as number) || 0);
  const growthValues = ctx.rows.map(r => (r[growthKey] as number) || 0);
  const achieveValues = ctx.rows.map(r => (r[achieveKey] as number) || 0);
  
  const salesStats = calculateStats(values);
  const growthStats = calculateStats(growthValues);
  const achieveStats = calculateStats(achieveValues);
  
  // Top performers in this category
  const topInCategory = getTopN(ctx.rows, actualKey as keyof TableRow, 3);
  const topList = topInCategory.map((r, i) => 
    `${i + 1}. ${r.entityName} - ${formatCurrency(r[actualKey] as number)}`
  ).join('\n');
  
  return {
    answer: `📦 **${label} Performance Analysis:**\n\n` +
      `**Sales Metrics:**\n` +
      `• Total: ${formatCurrency(salesStats.sum)}\n` +
      `• Average: ${formatCurrency(salesStats.avg)}\n` +
      `• Range: ${formatCurrency(salesStats.min)} - ${formatCurrency(salesStats.max)}\n\n` +
      `**Growth:** Avg ${formatPercent(growthStats.avg)}\n` +
      `**Achievement:** Avg ${achieveStats.avg.toFixed(1)}%\n\n` +
      `**Top 3 in ${label}:**\n${topList}`,
    chartSuggestion: 'bar',
    confidence: 'high',
  };
}

function analyzeGrowth(ctx: AnalysisContext): AnalysisResult {
  // Overall growth analysis
  const growthData = ctx.rows.map(r => ({
    name: r.entityName as string,
    growth: r.overall_growthPct as number,
  }));
  
  const positive = growthData.filter(d => d.growth > 0);
  const negative = growthData.filter(d => d.growth < 0);
  const zero = growthData.filter(d => d.growth === 0);
  
  const topGrowing = getTopN(ctx.rows, 'overall_growthPct', 5);
  const declining = getTopN(ctx.rows, 'overall_growthPct', 5, true).filter(r => (r.overall_growthPct as number) < 0);
  
  let answer = `📈 **Growth Analysis:**\n\n` +
    `**Distribution:**\n` +
    `• 🟢 Growing: ${positive.length} entities (${((positive.length / ctx.rows.length) * 100).toFixed(1)}%)\n` +
    `• 🔴 Declining: ${negative.length} entities (${((negative.length / ctx.rows.length) * 100).toFixed(1)}%)\n` +
    `• ⚪ Flat: ${zero.length} entities\n\n`;
  
  if (topGrowing.length > 0) {
    answer += `**Top Growing:**\n` + 
      topGrowing.slice(0, 3).map((r, i) => `${i + 1}. ${r.entityName} (${formatPercent(r.overall_growthPct as number)})`).join('\n') + '\n\n';
  }
  
  if (declining.length > 0) {
    answer += `**Declining:**\n` + 
      declining.slice(0, 3).map((r, i) => `${i + 1}. ${r.entityName} (${formatPercent(r.overall_growthPct as number)})`).join('\n');
  }
  
  return {
    answer,
    data: growthData,
    chartSuggestion: 'bar',
    confidence: 'high',
  };
}

function analyzeAchievement(ctx: AnalysisContext): AnalysisResult {
  const achievementData = ctx.rows.map(r => ({
    name: r.entityName as string,
    achievement: r.overall_achievementPct as number || 0,
  }));
  
  const overAchievers = achievementData.filter(d => d.achievement >= 100);
  const nearTarget = achievementData.filter(d => d.achievement >= 80 && d.achievement < 100);
  const belowTarget = achievementData.filter(d => d.achievement > 0 && d.achievement < 80);
  const noTarget = achievementData.filter(d => d.achievement === 0);
  
  const topAchievers = [...achievementData].sort((a, b) => b.achievement - a.achievement).slice(0, 5);
  
  return {
    answer: `🎯 **Target Achievement Analysis:**\n\n` +
      `**Performance Distribution:**\n` +
      `• 🏆 Over-achievers (≥100%): ${overAchievers.length} entities\n` +
      `• 📊 Near target (80-99%): ${nearTarget.length} entities\n` +
      `• ⚠️ Below target (<80%): ${belowTarget.length} entities\n` +
      `• ❓ No target set: ${noTarget.length} entities\n\n` +
      `**Top Achievers:**\n` +
      topAchievers.slice(0, 3).map((d, i) => `${i + 1}. ${d.name} (${d.achievement.toFixed(1)}%)`).join('\n'),
    chartSuggestion: 'bar',
    confidence: 'high',
  };
}

function compareCategories(ctx: AnalysisContext, cat1: string, cat2: string): AnalysisResult {
  const key1 = getCategoryKey(cat1);
  const key2 = getCategoryKey(cat2);
  
  if (!key1 || !key2) {
    return {
      answer: `❌ I couldn't recognize one or both categories. Please use: Project Wires, Flexibles, HDC, Dowells, FMEG, or Lumes.`,
      confidence: 'low',
    };
  }
  
  const label1 = getCategoryLabel(key1);
  const label2 = getCategoryLabel(key2);
  
  const sales1 = calculateStats(ctx.rows.map(r => (r[`${key1}_actualSales`] as number) || 0));
  const sales2 = calculateStats(ctx.rows.map(r => (r[`${key2}_actualSales`] as number) || 0));
  
  const growth1 = calculateStats(ctx.rows.map(r => (r[`${key1}_growthPct`] as number) || 0));
  const growth2 = calculateStats(ctx.rows.map(r => (r[`${key2}_growthPct`] as number) || 0));
  
  const winner = sales1.sum > sales2.sum ? label1 : label2;
  const growthWinner = growth1.avg > growth2.avg ? label1 : label2;
  
  return {
    answer: `⚖️ **${label1} vs ${label2} Comparison:**\n\n` +
      `| Metric | ${label1} | ${label2} |\n` +
      `|--------|----------|----------|\n` +
      `| Total Sales | ${formatCurrency(sales1.sum)} | ${formatCurrency(sales2.sum)} |\n` +
      `| Avg Sales | ${formatCurrency(sales1.avg)} | ${formatCurrency(sales2.avg)} |\n` +
      `| Avg Growth | ${formatPercent(growth1.avg)} | ${formatPercent(growth2.avg)} |\n\n` +
      `📊 **${winner}** leads in total sales.\n` +
      `📈 **${growthWinner}** has better average growth.`,
    chartSuggestion: 'bar',
    confidence: 'high',
  };
}

function analyzeZones(ctx: AnalysisContext): AnalysisResult {
  const zoneMap = new Map<string, { total: number; count: number; growth: number }>();
  
  ctx.rows.forEach(row => {
    const zone = row.zone as string;
    if (!zone) return;
    
    const current = zoneMap.get(zone) || { total: 0, count: 0, growth: 0 };
    current.total += (row.overall_actualSales as number) || 0;
    current.growth += (row.overall_growthPct as number) || 0;
    current.count += 1;
    zoneMap.set(zone, current);
  });
  
  const zoneData = Array.from(zoneMap.entries())
    .map(([zone, data]) => ({
      zone,
      total: data.total,
      avgGrowth: data.count > 0 ? data.growth / data.count : 0,
      count: data.count,
    }))
    .sort((a, b) => b.total - a.total);
  
  const breakdown = zoneData
    .map(z => `• **${z.zone}**: ${formatCurrency(z.total)} | ${z.count} entities | Avg Growth: ${formatPercent(z.avgGrowth)}`)
    .join('\n');
  
  return {
    answer: `🗺️ **Zone-wise Performance:**\n\n${breakdown}\n\n💡 Focus on zones with high entity count but lower average performance for potential improvement.`,
    data: zoneData,
    chartSuggestion: 'bar',
    confidence: 'high',
  };
}

function countEntities(ctx: AnalysisContext): AnalysisResult {
  const distributors = ctx.rows.filter(r => r.entityType === 'DISTRIBUTOR');
  const customers = ctx.rows.filter(r => r.entityType === 'CUSTOMER');
  
  return {
    answer: `📊 **Entity Count:**\n\n` +
      `• **Total Entities:** ${ctx.rows.length}\n` +
      `• **Distributors:** ${distributors.length}\n` +
      `• **Customers:** ${customers.length}\n\n` +
      `Currently viewing data with ${ctx.filters.zone ? `Zone: ${ctx.filters.zone}` : 'all zones'}.`,
    confidence: 'high',
  };
}

function generateSummary(ctx: AnalysisContext): AnalysisResult {
  const totalSales = calculateStats(ctx.rows.map(r => (r.overall_actualSales as number) || 0));
  const avgGrowth = calculateStats(ctx.rows.map(r => (r.overall_growthPct as number) || 0));
  
  const growing = ctx.rows.filter(r => (r.overall_growthPct as number) > 0).length;
  const declining = ctx.rows.filter(r => (r.overall_growthPct as number) < 0).length;
  
  const topCategory = CATEGORIES.map(cat => ({
    label: cat.label,
    total: calculateStats(ctx.rows.map(r => (r[`${cat.key}_actualSales`] as number) || 0)).sum,
  })).sort((a, b) => b.total - a.total)[0];
  
  return {
    answer: `📋 **Report Summary:**\n\n` +
      `**Overview:**\n` +
      `• ${ctx.rows.length} entities in current view\n` +
      `• Total Sales: ${formatCurrency(totalSales.sum)}\n` +
      `• Average Growth: ${formatPercent(avgGrowth.avg)}\n\n` +
      `**Health Check:**\n` +
      `• 🟢 ${growing} entities growing (${((growing / ctx.rows.length) * 100).toFixed(0)}%)\n` +
      `• 🔴 ${declining} entities declining (${((declining / ctx.rows.length) * 100).toFixed(0)}%)\n\n` +
      `**Top Category:** ${topCategory.label} with ${formatCurrency(topCategory.total)}\n\n` +
      `💡 *Try asking about specific categories, top performers, or growth trends for deeper insights!*`,
    confidence: 'high',
  };
}

function showHelp(): AnalysisResult {
  return {
    answer: `🤖 **I can help you analyze this report! Try asking:**\n\n` +
      `**Performance:**\n` +
      `• "Who are the top 5 performers?"\n` +
      `• "Show me bottom performers"\n` +
      `• "What are the total sales?"\n\n` +
      `**Categories:**\n` +
      `• "How is Project Wires performing?"\n` +
      `• "Compare HDC vs Flexibles"\n` +
      `• "Which category has highest sales?"\n\n` +
      `**Analysis:**\n` +
      `• "Show growth analysis"\n` +
      `• "Target achievement summary"\n` +
      `• "Zone-wise breakdown"\n` +
      `• "Give me a summary"\n\n` +
      `**Counts:**\n` +
      `• "How many distributors?"\n` +
      `• "Count entities by type"`,
    confidence: 'high',
  };
}

// ============================================
// Main Analysis Function
// ============================================

export function analyzeQuestion(question: string, context: AnalysisContext): AnalysisResult {
  const q = question.toLowerCase().trim();
  
  // Check for help
  if (PATTERNS.help.test(q)) {
    return showHelp();
  }
  
  // Check for summary
  if (PATTERNS.summary.test(q)) {
    return generateSummary(context);
  }
  
  // Check for category comparison
  const compareMatch = q.match(PATTERNS.categoryCompare);
  if (compareMatch) {
    return compareCategories(context, compareMatch[1], compareMatch[2]);
  }
  
  // Check for specific category
  const categoryMatch = q.match(PATTERNS.specificCategory);
  if (categoryMatch) {
    const catKey = getCategoryKey(categoryMatch[1]);
    if (catKey) {
      return analyzeCategory(context, catKey);
    }
  }
  
  // Check for top performers
  const topMatch = q.match(PATTERNS.topPerformers);
  if (topMatch) {
    const count = topMatch[1] ? parseInt(topMatch[1]) : 5;
    return analyzeTopPerformers(context, Math.min(count, 20));
  }
  
  // Check for bottom performers
  const bottomMatch = q.match(PATTERNS.bottomPerformers);
  if (bottomMatch) {
    const count = bottomMatch[1] ? parseInt(bottomMatch[1]) : 5;
    return analyzeBottomPerformers(context, Math.min(count, 20));
  }
  
  // Check for total sales
  if (PATTERNS.totalSales.test(q)) {
    return analyzeTotalSales(context);
  }
  
  // Check for growth analysis
  if (PATTERNS.growthAnalysis.test(q)) {
    return analyzeGrowth(context);
  }
  
  // Check for achievement analysis
  if (PATTERNS.achievementAnalysis.test(q)) {
    return analyzeAchievement(context);
  }
  
  // Check for zone analysis
  if (PATTERNS.zoneAnalysis.test(q)) {
    return analyzeZones(context);
  }
  
  // Check for entity count
  if (PATTERNS.countEntities.test(q)) {
    return countEntities(context);
  }
  
  // Check for average
  if (PATTERNS.averageSales.test(q)) {
    const stats = calculateStats(context.rows.map(r => (r.overall_actualSales as number) || 0));
    return {
      answer: `📊 **Average Sales:** ${formatCurrency(stats.avg)} per entity\n\nBased on ${stats.count} entities in the current view.`,
      confidence: 'high',
    };
  }
  
  // Check for max/min
  if (PATTERNS.maxMin.test(q)) {
    const isMax = /max|highest/i.test(q);
    const sorted = [...context.rows].sort((a, b) => {
      const aVal = (a.overall_actualSales as number) || 0;
      const bVal = (b.overall_actualSales as number) || 0;
      return isMax ? bVal - aVal : aVal - bVal;
    });
    const entity = sorted[0];
    
    return {
      answer: `🏆 **${isMax ? 'Highest' : 'Lowest'} Sales:**\n\n` +
        `**${entity.entityName}**\n` +
        `• Sales: ${formatCurrency(entity.overall_actualSales as number)}\n` +
        `• Growth: ${formatPercent(entity.overall_growthPct as number)}\n` +
        `• Zone: ${entity.zone}`,
      confidence: 'high',
    };
  }
  
  // Default response
  return {
    answer: `🤔 I'm not sure how to answer that specific question. Here are some things you can ask:\n\n` +
      `• "Top 5 performers"\n` +
      `• "Total sales breakdown"\n` +
      `• "How is HDC performing?"\n` +
      `• "Compare Flexibles vs Dowells"\n` +
      `• "Growth analysis"\n` +
      `• "Summary"\n\n` +
      `Or type "help" for more options!`,
    confidence: 'low',
  };
}

// ============================================
// Suggested Questions
// ============================================

export const SUGGESTED_QUESTIONS = [
  "Who are the top 5 performers?",
  "Show me total sales breakdown",
  "How is Project Wires performing?",
  "Compare HDC vs Flexibles",
  "Growth analysis",
  "Zone-wise breakdown",
  "Target achievement summary",
  "Give me a summary",
];

