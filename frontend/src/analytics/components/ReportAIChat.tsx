/**
 * ReportAIChat Component
 * 
 * AI-powered chat assistant for analyzing report data.
 * Now powered by backend LLM service for intelligent SQL-based analysis.
 * 
 * Features:
 * - Natural language questions converted to SQL
 * - Real-time database queries
 * - Markdown-formatted responses
 * - Query timing and cost tracking
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ChevronDown,
  Lightbulb,
  Loader2,
  Trash2,
  Minimize2,
  Database,
  Clock,
  Code2,
  AlertCircle,
} from 'lucide-react';

// ============================================
// Types
// ============================================

interface VisualizationDataItem {
  label: string;
  value: number;
  percentage: number;
}

interface VisualizationData {
  type: 'pie' | 'bar' | 'donut' | 'none';
  title: string;
  data: VisualizationDataItem[];
  total: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sql?: string;
  timing?: {
    sqlGenerationMs: number;
    sqlExecutionMs: number;
    totalMs: number;
  };
  status?: 'success' | 'error' | 'no_results';
  visualization?: VisualizationData;
}

interface FilterState {
  itemGroup?: string;
  material?: string;
  brand?: string;
  customerState?: string[];
  industry?: string[];
  customerCategory?: string;
  customerType?: string;
  period?: string;
}

interface TimeState {
  fiscalYear: string;
  period: string;
}

interface ReportAIChatProps {
  filters?: FilterState;
  time?: TimeState;
  reportName?: string;
}

interface ChatApiResponse {
  status: string;
  answer: string;
  sql?: string;
  data?: any[];
  rowCount: number;
  error?: string;
  visualization?: VisualizationData;
  timing: {
    sqlGenerationMs: number;
    sqlExecutionMs: number;
    answerFormattingMs: number;
    totalMs: number;
  };
  usage: {
    tokensUsed: number;
    estimatedCostUsd: number;
  };
}

// ============================================
// Suggested Questions
// ============================================

const SUGGESTED_QUESTIONS = [
  "Top 5 customers by sales",
  "Sales by state",
  "Who has negative margin?",
  "Total sales of building wires",
  "Compare building wires vs LT cables",
  "Monthly sales trend",
  "Top distributors in Maharashtra",
  "Average order value",
];

// ============================================
// Markdown Parser
// ============================================

function parseMarkdown(text: string): string {
  return text
    // Headers
    .replace(/^### (.+)$/gm, '<h4 class="font-semibold text-gray-800 mt-3 mb-1 text-sm">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="font-semibold text-gray-900 mt-3 mb-2">$1</h3>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>')
    // Code
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">$1</code>')
    // List items with dash
    .replace(/^- (.+)$/gm, '<div class="flex gap-2 items-start ml-2"><span class="text-purple-500 mt-1">•</span><span>$1</span></div>')
    // List items with bullet
    .replace(/^• (.+)$/gm, '<div class="flex gap-2 items-start ml-2"><span class="text-purple-500 mt-1">•</span><span>$1</span></div>')
    // Numbered lists
    .replace(/^(\d+)\. (.+)$/gm, '<div class="flex gap-2 items-start"><span class="text-purple-600 font-medium min-w-[1.5rem]">$1.</span><span>$2</span></div>')
    // Currency formatting (₹)
    .replace(/₹([\d,]+(?:\.\d{2})?)/g, '<span class="font-mono text-green-700">₹$1</span>')
    // Paragraphs
    .replace(/\n\n/g, '</p><p class="mt-2">')
    .replace(/\n/g, '<br/>');
}

// ============================================
// Pie Chart Component
// ============================================

const PIE_COLORS = [
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#f59e0b', // Amber
  '#10b981', // Emerald
  '#f43f5e', // Rose
  '#6366f1', // Indigo
  '#84cc16', // Lime
  '#ec4899', // Pink
  '#14b8a6', // Teal
  '#f97316', // Orange
];

interface PieChartProps {
  data: VisualizationDataItem[];
  title: string;
  total: number;
}

function PieChart({ data, title, total }: PieChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  
  // Calculate pie slices
  const size = 140;
  const center = size / 2;
  const radius = 55;
  
  let cumulativeAngle = -90; // Start from top
  
  const slices = data.map((item, index) => {
    const angle = (item.percentage / 100) * 360;
    const startAngle = cumulativeAngle;
    const endAngle = cumulativeAngle + angle;
    cumulativeAngle = endAngle;
    
    // Convert angles to radians
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    
    // Calculate arc points
    const x1 = center + radius * Math.cos(startRad);
    const y1 = center + radius * Math.sin(startRad);
    const x2 = center + radius * Math.cos(endRad);
    const y2 = center + radius * Math.sin(endRad);
    
    // Large arc flag (1 if angle > 180)
    const largeArc = angle > 180 ? 1 : 0;
    
    // Path for the slice
    const path = `M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
    
    return {
      path,
      color: PIE_COLORS[index % PIE_COLORS.length],
      ...item,
      index,
    };
  });

  // Format currency
  const formatValue = (value: number) => {
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
    if (value >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
    return `₹${value.toFixed(0)}`;
  };

  return (
    <div className="bg-gradient-to-br from-gray-50 to-white rounded-xl p-4 border border-gray-100 shadow-sm mt-3">
      {/* Title */}
      <h4 className="text-sm font-semibold text-gray-800 mb-3 text-center">{title}</h4>
      
      <div className="flex items-center gap-4">
        {/* Pie Chart SVG */}
        <div className="relative flex-shrink-0">
          <svg width={size} height={size} className="transform -rotate-0">
            {slices.map((slice) => (
              <path
                key={slice.index}
                d={slice.path}
                fill={slice.color}
                stroke="white"
                strokeWidth="2"
                className="transition-all duration-200 cursor-pointer"
                style={{
                  opacity: hoveredIndex === null || hoveredIndex === slice.index ? 1 : 0.4,
                  transform: hoveredIndex === slice.index ? 'scale(1.05)' : 'scale(1)',
                  transformOrigin: 'center',
                }}
                onMouseEnter={() => setHoveredIndex(slice.index)}
                onMouseLeave={() => setHoveredIndex(null)}
              />
            ))}
            {/* Center circle for donut effect */}
            <circle cx={center} cy={center} r={30} fill="white" />
            {/* Center text */}
            <text
              x={center}
              y={center - 6}
              textAnchor="middle"
              className="text-[10px] fill-gray-500 font-medium"
            >
              Total
            </text>
            <text
              x={center}
              y={center + 8}
              textAnchor="middle"
              className="text-xs fill-gray-800 font-bold"
            >
              {formatValue(total)}
            </text>
          </svg>
        </div>
        
        {/* Legend */}
        <div className="flex-1 space-y-1.5 max-h-[140px] overflow-y-auto">
          {slices.map((slice) => (
            <div
              key={slice.index}
              className={`flex items-center gap-2 px-2 py-1 rounded-lg transition-all duration-200 cursor-pointer ${
                hoveredIndex === slice.index ? 'bg-gray-100' : ''
              }`}
              onMouseEnter={() => setHoveredIndex(slice.index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: slice.color }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-gray-700 truncate">
                  {slice.label}
                </div>
                <div className="text-[10px] text-gray-500">
                  {formatValue(slice.value)} ({slice.percentage}%)
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================
// API Service
// ============================================

async function askQuestion(
  question: string,
  filters?: FilterState,
  time?: TimeState
): Promise<ChatApiResponse> {
  const response = await fetch('/api/v1/reports/sales-analytics/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      filters: filters || null,
      time: time || null,
      includeSql: true,
      includeData: false,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to get response');
  }

  return response.json();
}

// ============================================
// Main Component
// ============================================

export default function ReportAIChat({ filters, time, reportName = 'Sales Analytics' }: ReportAIChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [showSql, setShowSql] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);
  
  // Handle sending a message
  const handleSend = useCallback(async (question?: string) => {
    const text = question || input.trim();
    if (!text) return;
    
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setShowSuggestions(false);
    setIsTyping(true);
    
    try {
      // Call the AI API
      const response = await askQuestion(text, filters, time);
    
    // Add assistant message
    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
        content: response.answer,
      timestamp: new Date(),
        sql: response.sql,
        timing: {
          sqlGenerationMs: response.timing.sqlGenerationMs,
          sqlExecutionMs: response.timing.sqlExecutionMs,
          totalMs: response.timing.totalMs,
        },
        status: response.status === 'success' ? 'success' : 
                response.status === 'no_results' ? 'no_results' : 'error',
      visualization: response.visualization,
    };
    
    setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      // Add error message
      const errorMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
        status: 'error',
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
    setIsTyping(false);
    }
  }, [input, filters, time]);
  
  // Handle keyboard submit
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  // Clear chat
  const handleClear = () => {
    setMessages([]);
    setShowSuggestions(true);
    setShowSql(null);
  };
  
  // Toggle chat
  const toggleChat = () => {
    if (isMinimized) {
      setIsMinimized(false);
    } else {
      setIsOpen(!isOpen);
    }
  };
  
  return (
    <>
      {/* Floating Button */}
      <button
        onClick={toggleChat}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 hover:scale-110 ${
          isOpen 
            ? 'bg-gray-800 text-white rotate-0' 
            : 'bg-gradient-to-br from-purple-600 to-indigo-600 text-white'
        }`}
        style={{
          boxShadow: isOpen 
            ? '0 4px 20px rgba(0,0,0,0.2)' 
            : '0 4px 20px rgba(124, 58, 237, 0.4)',
        }}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <div className="relative">
            <MessageSquare className="w-6 h-6" />
            <Sparkles className="w-3 h-3 absolute -top-1 -right-1 text-yellow-300" />
          </div>
        )}
      </button>
      
      {/* Chat Panel */}
      {isOpen && (
        <div 
          className={`fixed bottom-24 right-6 z-50 bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 ${
            isMinimized ? 'w-80 h-14' : 'w-[420px] h-[36rem]'
          }`}
          style={{
            boxShadow: '0 10px 40px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05)',
          }}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-4 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">AI Data Assistant</h3>
                <p className="text-[10px] text-white/70 flex items-center gap-1">
                  <Database className="w-3 h-3" />
                  Powered by GPT-4
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && !isMinimized && (
                <button
                  onClick={handleClear}
                  className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  title="Clear chat"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
              >
                {isMinimized ? <ChevronDown className="w-4 h-4 rotate-180" /> : <Minimize2 className="w-4 h-4" />}
              </button>
            </div>
          </div>
          
          {!isMinimized && (
            <>
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-50 to-white">
                {/* Welcome Message */}
                {messages.length === 0 && (
                  <div className="text-center py-4">
                    <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-gradient-to-br from-purple-100 to-indigo-100 flex items-center justify-center">
                      <Sparkles className="w-7 h-7 text-purple-600" />
                    </div>
                    <h4 className="font-semibold text-gray-800 mb-1">Hi! I'm your AI Data Assistant</h4>
                    <p className="text-sm text-gray-500 mb-2">
                      Ask me anything about {reportName}
                    </p>
                    <p className="text-xs text-gray-400">
                      I can query the database and analyze your sales data in real-time
                    </p>
                  </div>
                )}
                
                {/* Suggested Questions */}
                {showSuggestions && messages.length === 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
                      <Lightbulb className="w-3.5 h-3.5" />
                      <span>Try asking</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {SUGGESTED_QUESTIONS.map((q, i) => (
                        <button
                          key={i}
                          onClick={() => handleSend(q)}
                          className="px-3 py-1.5 text-xs bg-white border border-gray-200 rounded-full hover:border-purple-300 hover:bg-purple-50 transition-colors text-gray-700"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Messages */}
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-2 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    {/* Avatar */}
                    <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center ${
                      message.role === 'user' 
                        ? 'bg-gray-800 text-white' 
                        : message.status === 'error' 
                          ? 'bg-red-500 text-white'
                        : 'bg-gradient-to-br from-purple-500 to-indigo-500 text-white'
                    }`}>
                      {message.role === 'user' ? (
                        <User className="w-4 h-4" />
                      ) : message.status === 'error' ? (
                        <AlertCircle className="w-4 h-4" />
                      ) : (
                        <Bot className="w-4 h-4" />
                      )}
                    </div>
                    
                    {/* Message Content */}
                    <div className={`max-w-[85%] ${message.role === 'user' ? 'text-right' : ''}`}>
                      <div className={`inline-block px-3 py-2 rounded-2xl text-sm ${
                        message.role === 'user'
                          ? 'bg-gray-800 text-white rounded-tr-md'
                          : message.status === 'error'
                            ? 'bg-red-50 border border-red-200 text-red-700 rounded-tl-md'
                          : 'bg-white border border-gray-100 text-gray-700 rounded-tl-md shadow-sm'
                      }`}>
                        {message.role === 'user' ? (
                          message.content
                        ) : (
                          <div 
                            className="prose prose-sm max-w-none [&_strong]:text-purple-700"
                            dangerouslySetInnerHTML={{ __html: parseMarkdown(message.content) }}
                          />
                        )}
                      </div>
                      
                      {/* Message metadata for assistant */}
                      {message.role === 'assistant' && message.status !== 'error' && (
                        <div className="flex items-center gap-3 mt-1.5 text-[10px] text-gray-400">
                          {message.timing && (
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {(message.timing.totalMs / 1000).toFixed(1)}s
                            </span>
                          )}
                          {message.sql && (
                            <button
                              onClick={() => setShowSql(showSql === message.id ? null : message.id)}
                              className="flex items-center gap-1 hover:text-purple-600 transition-colors"
                            >
                              <Code2 className="w-3 h-3" />
                              {showSql === message.id ? 'Hide SQL' : 'Show SQL'}
                            </button>
                          )}
                        </div>
                      )}
                      
                      {/* SQL Display */}
                      {showSql === message.id && message.sql && (
                        <div className="mt-2 p-2 bg-gray-900 rounded-lg text-xs font-mono text-gray-300 overflow-x-auto">
                          <pre className="whitespace-pre-wrap">{message.sql}</pre>
                        </div>
                      )}
                      
                      {/* Visualization (Pie Chart) */}
                      {message.visualization && message.visualization.type === 'pie' && message.visualization.data.length > 0 && (
                        <PieChart
                          data={message.visualization.data}
                          title={message.visualization.title}
                          total={message.visualization.total}
                        />
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Typing Indicator */}
                {isTyping && (
                  <div className="flex gap-2 items-start">
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 text-white flex items-center justify-center">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                        <span className="text-xs text-gray-400">Querying database...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
              
              {/* Input Area */}
              <div className="p-3 border-t border-gray-100 bg-white flex-shrink-0">
                <div className="flex gap-2 items-center">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about your sales data..."
                    disabled={isTyping}
                    className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 transition-all"
                  />
                  <button
                    onClick={() => handleSend()}
                    disabled={!input.trim() || isTyping}
                    className="w-10 h-10 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:scale-105 transition-all"
                  >
                    {isTyping ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </button>
                </div>
                <p className="text-[10px] text-gray-400 mt-2 text-center">
                  AI-powered • Real-time database queries • {time?.period || 'All periods'}
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
