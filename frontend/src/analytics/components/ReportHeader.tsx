/**
 * ReportHeader Component
 * 
 * Displays the report title, description, last updated timestamp,
 * and action buttons (Export, Share, Refresh).
 */

import { useState } from 'react';
import { Download, Share2, RefreshCw, Clock, ChevronDown } from 'lucide-react';
import type { ReportConfig, MetaResponse, FeaturesConfig } from '../types';
import { formatTimestamp, formatRelativeTime } from '../utils/formatters';

interface ReportHeaderProps {
  config: ReportConfig;
  meta?: MetaResponse;
  isLoading?: boolean;
  onRefresh?: () => void;
  onExport?: (format: 'csv' | 'xlsx') => void;
  onShare?: () => void;
}

export default function ReportHeader({
  config,
  meta,
  isLoading,
  onRefresh,
  onExport,
  onShare,
}: ReportHeaderProps) {
  const [showExportMenu, setShowExportMenu] = useState(false);
  
  const features: FeaturesConfig = meta?.features || config.features || {};
  
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-start justify-between">
        {/* Title and Description */}
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{config.title}</h1>
          {config.description && (
            <p className="mt-1 text-sm text-gray-500">{config.description}</p>
          )}
          
          {/* Last Updated */}
          {meta?.lastUpdatedAt && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-gray-400">
              <Clock className="w-3.5 h-3.5" />
              <span title={formatTimestamp(meta.lastUpdatedAt)}>
                Data updated: {formatRelativeTime(meta.lastUpdatedAt)}
              </span>
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center gap-2 ml-4">
          {/* Refresh Button */}
          {features.refresh !== false && onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Refresh data"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          )}
          
          {/* Share Button */}
          {features.share && onShare && (
            <button
              onClick={onShare}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              title="Share report"
            >
              <Share2 className="w-4 h-4" />
              <span className="hidden sm:inline">Share</span>
            </button>
          )}
          
          {/* Export Button with Dropdown */}
          {features.export && onExport && (
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              
              {showExportMenu && (
                <>
                  {/* Backdrop */}
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowExportMenu(false)}
                  />
                  
                  {/* Dropdown Menu */}
                  <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                    <button
                      onClick={() => {
                        onExport('csv');
                        setShowExportMenu(false);
                      }}
                      className="w-full px-4 py-2 text-sm text-left text-gray-700 hover:bg-gray-50 first:rounded-t-lg"
                    >
                      Export as CSV
                    </button>
                    <button
                      onClick={() => {
                        onExport('xlsx');
                        setShowExportMenu(false);
                      }}
                      className="w-full px-4 py-2 text-sm text-left text-gray-700 hover:bg-gray-50 last:rounded-b-lg"
                    >
                      Export as Excel
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

