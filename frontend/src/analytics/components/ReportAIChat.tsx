/**
 * ReportAIChat Component
 * 
 * Floating AI chat assistant for analyzing report data.
 * Features:
 * - Natural language questions about report data
 * - Markdown-formatted responses
 * - Suggested questions
 * - Animated UI with smooth transitions
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
} from 'lucide-react';
import type { TableRow, KpiCardData } from '../types';
import { analyzeQuestion, SUGGESTED_QUESTIONS, type AnalysisContext } from '../utils/dataAnalyzer';

// ============================================
// Types
// ============================================

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: 'high' | 'medium' | 'low';
}

interface ReportAIChatProps {
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

// ============================================
// Markdown Parser (Simple)
// ============================================

function parseMarkdown(text: string): string {
  return text
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
    // Tables (simple)
    .replace(/\|([^|]+)\|([^|]+)\|([^|]+)\|/g, (_, c1, c2, c3) => 
      `<div class="grid grid-cols-3 gap-2 text-xs py-1 border-b border-gray-100"><span>${c1.trim()}</span><span>${c2.trim()}</span><span>${c3.trim()}</span></div>`
    )
    // List items
    .replace(/^• (.+)$/gm, '<div class="flex gap-2 items-start"><span class="text-purple-500">•</span><span>$1</span></div>')
    // Numbered lists
    .replace(/^(\d+)\. (.+)$/gm, '<div class="flex gap-2 items-start"><span class="text-purple-600 font-medium min-w-[1.2rem]">$1.</span><span>$2</span></div>')
    // Line breaks
    .replace(/\n\n/g, '</p><p class="mt-3">')
    .replace(/\n/g, '<br/>');
}

// ============================================
// Main Component
// ============================================

export default function ReportAIChat({ rows, kpis, filters, aggregation }: ReportAIChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  
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
  
  // Build context for analysis
  const buildContext = useCallback((): AnalysisContext => ({
    rows,
    kpis,
    filters,
    aggregation,
  }), [rows, kpis, filters, aggregation]);
  
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
    
    // Simulate AI thinking delay
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 800));
    
    // Get analysis result
    const context = buildContext();
    const result = analyzeQuestion(text, context);
    
    // Add assistant message
    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: result.answer,
      timestamp: new Date(),
      confidence: result.confidence,
    };
    
    setMessages(prev => [...prev, assistantMessage]);
    setIsTyping(false);
  }, [input, buildContext]);
  
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
            isMinimized ? 'w-80 h-14' : 'w-96 h-[32rem]'
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
                <p className="text-[10px] text-white/70">Ask about your report</p>
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
                  <div className="text-center py-6">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-100 to-indigo-100 flex items-center justify-center">
                      <Sparkles className="w-8 h-8 text-purple-600" />
                    </div>
                    <h4 className="font-semibold text-gray-800 mb-1">Hi! I'm your Data Assistant</h4>
                    <p className="text-sm text-gray-500 mb-4">
                      Ask me anything about the {rows.length} entities in this report
                    </p>
                  </div>
                )}
                
                {/* Suggested Questions */}
                {showSuggestions && messages.length === 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
                      <Lightbulb className="w-3.5 h-3.5" />
                      <span>Suggested questions</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {SUGGESTED_QUESTIONS.slice(0, 6).map((q, i) => (
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
                        : 'bg-gradient-to-br from-purple-500 to-indigo-500 text-white'
                    }`}>
                      {message.role === 'user' ? (
                        <User className="w-4 h-4" />
                      ) : (
                        <Bot className="w-4 h-4" />
                      )}
                    </div>
                    
                    {/* Message Content */}
                    <div className={`max-w-[85%] ${message.role === 'user' ? 'text-right' : ''}`}>
                      <div className={`inline-block px-3 py-2 rounded-2xl text-sm ${
                        message.role === 'user'
                          ? 'bg-gray-800 text-white rounded-tr-md'
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
                      {message.confidence && message.role === 'assistant' && (
                        <div className={`text-[10px] mt-1 ${
                          message.confidence === 'high' ? 'text-green-600' :
                          message.confidence === 'medium' ? 'text-amber-600' : 'text-gray-400'
                        }`}>
                          {message.confidence === 'high' ? '✓ High confidence' :
                           message.confidence === 'medium' ? '~ Medium confidence' : '? Try rephrasing'}
                        </div>
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
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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
                    placeholder="Ask about your data..."
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
                  AI analysis is based on {rows.length} entities • Filters applied
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}

