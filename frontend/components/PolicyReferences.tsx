import React from 'react';
import { ExternalLink, AlertTriangle, CheckCircle } from 'lucide-react';
import { PolicyReference } from '@/types/policy';

interface PolicyReferencesProps {
  references: PolicyReference[];
  className?: string;
}

export const PolicyReferences: React.FC<PolicyReferencesProps> = ({ 
  references, 
  className = '' 
}) => {
  if (!references || references.length === 0) {
    return null;
  }

  const getReliabilityIcon = (reliability: string) => {
    switch (reliability) {
      case 'high':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'medium':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'low':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <ExternalLink className="h-4 w-4 text-gray-600" />;
    }
  };

  const getReliabilityBadge = (sourceType: string, reliability: string) => {
    if (sourceType === 'official') {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          公式
        </span>
      );
    }
    
    if (sourceType === 'gemini_search') {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          検索収集
        </span>
      );
    }

    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        {sourceType}
      </span>
    );
  };

  const getDisclaimerText = (sourceType: string) => {
    if (sourceType === 'gemini_search') {
      return 'この情報はGemini検索により収集されました。参考程度にとどめ、詳細は公式サイトで必ずご確認ください。';
    }
    return null;
  };

  return (
    <div className={`bg-gray-50 rounded-lg p-4 ${className}`}>
      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
        <ExternalLink className="h-4 w-4 mr-2" />
        参考資料・出典
      </h4>
      
      <div className="space-y-3">
        {references.map((ref, index) => (
          <div key={index} className="bg-white rounded-md p-3 border border-gray-200">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                {getReliabilityIcon(ref.reliability)}
                <span className="text-sm font-medium text-gray-900">
                  {ref.description}
                </span>
                {getReliabilityBadge(ref.source_type, ref.reliability)}
              </div>
            </div>
            
            <a
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 underline break-all"
            >
              {ref.url}
            </a>
            
            {getDisclaimerText(ref.source_type) && (
              <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                <AlertTriangle className="h-3 w-3 inline mr-1" />
                {getDisclaimerText(ref.source_type)}
              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="mt-3 text-xs text-gray-500">
        ※ 参考資料は政策理解の補助として提供されています。投票の際は必ず各政党の公式情報をご確認ください。
      </div>
    </div>
  );
};

export default PolicyReferences;