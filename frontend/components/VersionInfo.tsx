'use client';

import { useState } from 'react';
import { Info } from 'lucide-react';
import getConfig from 'next/config';

interface VersionData {
  version: string;
  buildTime: string;
  gitCommit: string;
  environment: string;
}

export default function VersionInfo() {
  const [isOpen, setIsOpen] = useState(false);
  
  // Get version information from Next.js config
  const { publicRuntimeConfig } = getConfig() || { publicRuntimeConfig: {} };
  
  const versionData: VersionData = {
    version: publicRuntimeConfig?.version || '1.0.0',
    buildTime: publicRuntimeConfig?.buildTime || new Date().toISOString(),
    gitCommit: publicRuntimeConfig?.gitCommit || 'local',
    environment: process.env.NODE_ENV || 'development'
  };

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Tokyo'
      });
    } catch {
      return isoString;
    }
  };

  const shortCommit = versionData.gitCommit.substring(0, 7);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Version Badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs rounded-md transition-colors border border-gray-300"
        title="バージョン情報を表示"
      >
        <Info className="h-3 w-3" />
        <span>v{versionData.version}</span>
      </button>

      {/* Version Details Modal */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Modal */}
          <div className="absolute bottom-10 right-0 bg-white rounded-lg shadow-lg border border-gray-200 p-4 min-w-80 z-50">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">システム情報</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">バージョン:</span>
                <span className="font-mono font-medium">v{versionData.version}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">ビルド日時:</span>
                <span className="font-mono text-xs">{formatDate(versionData.buildTime)}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">コミット:</span>
                <span className="font-mono text-xs">{shortCommit}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">環境:</span>
                <span className={`font-medium ${
                  versionData.environment === 'production' ? 'text-green-600' : 'text-blue-600'
                }`}>
                  {versionData.environment}
                </span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                日本の政治議事録横断検索システム
              </p>
              <p className="text-xs text-gray-400 mt-1">
                🤖 Generated with Claude Code
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}