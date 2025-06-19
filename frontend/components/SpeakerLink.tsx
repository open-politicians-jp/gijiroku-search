'use client';

import React, { useState, useEffect } from 'react';
import { ExternalLink, User } from 'lucide-react';
import { getSpeakerProfileLink } from '@/lib/legislators-linker';

interface SpeakerLinkProps {
  speakerName: string;
  className?: string;
}

interface SpeakerLinkData {
  name: string;
  isLinked: boolean;
  linkData?: {
    name: string;
    house: string;
    party: string;
    district: string;
    profileUrl: string;
  };
}

export default function SpeakerLink({ speakerName, className = "" }: SpeakerLinkProps) {
  const [linkData, setLinkData] = useState<SpeakerLinkData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!speakerName) return;

    const fetchLinkData = async () => {
      setLoading(true);
      try {
        const data = await getSpeakerProfileLink(speakerName);
        setLinkData(data);
      } catch (error) {
        console.error('議員リンク取得エラー:', error);
        setLinkData({
          name: speakerName,
          isLinked: false
        });
      } finally {
        setLoading(false);
      }
    };

    fetchLinkData();
  }, [speakerName]);

  if (loading) {
    return (
      <span className={`${className} text-gray-500`}>
        {speakerName}
      </span>
    );
  }

  if (!linkData || !linkData.isLinked) {
    return (
      <span className={className}>
        {speakerName || '不明'}
      </span>
    );
  }

  return (
    <div className="inline-flex items-center gap-2">
      <a
        href={linkData.linkData?.profileUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={`${className} hover:text-blue-600 transition-colors inline-flex items-center gap-1 group`}
        title={`${linkData.linkData?.house} ${linkData.linkData?.district} (${linkData.linkData?.party})`}
      >
        <span className="font-medium">
          {linkData.name}
        </span>
        <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
      </a>
      
      {/* 議員情報のツールチップ的表示 */}
      {linkData.linkData && (
        <div className="hidden sm:inline-flex items-center gap-1 text-xs text-gray-500">
          <span className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">
            {linkData.linkData.house === '衆議院' ? '衆' : '参'}
          </span>
          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
            {linkData.linkData.party}
          </span>
        </div>
      )}
    </div>
  );
}

// メモ化されたバージョンも提供
export const MemoizedSpeakerLink = React.memo(SpeakerLink);