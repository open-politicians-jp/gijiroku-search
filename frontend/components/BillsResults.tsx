'use client';

import { ExternalLink, Calendar, Building, Tag, FileText, User } from 'lucide-react';
import { Bill } from '@/types';

interface BillsResultsProps {
  bills: Bill[];
  total: number;
  loading?: boolean;
}

export default function BillsResults({ bills, total, loading = false }: BillsResultsProps) {
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-3"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/4 mb-2"></div>
              <div className="h-16 bg-gray-200 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (bills.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 text-center py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <p className="text-gray-500">検索条件に一致する法案が見つかりませんでした。</p>
          <p className="text-sm text-gray-400 mt-2">
            検索キーワードや条件を変更してお試しください。
          </p>
        </div>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    try {
      return new Date(dateStr).toLocaleDateString('ja-JP');
    } catch {
      return dateStr;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted':
        return 'bg-blue-100 text-blue-800';
      case 'under_review':
        return 'bg-yellow-100 text-yellow-800';
      case 'committee_review':
        return 'bg-orange-100 text-orange-800';
      case 'passed':
        return 'bg-green-100 text-green-800';
      case 'enacted':
        return 'bg-emerald-100 text-emerald-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'abandoned':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (statusNormalized: string, originalStatus: string) => {
    const statusMap: Record<string, string> = {
      'submitted': '提出',
      'under_review': '審議中',
      'committee_referral': '委員会付託',
      'committee_review': '委員会審査中',
      'passed': '可決',
      'rejected': '否決',
      'continued': '継続審議',
      'abandoned': '廃案',
      'enacted': '成立',
      'promulgated': '公布'
    };
    
    return statusMap[statusNormalized] || originalStatus;
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      {/* 検索結果ヘッダー */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          提出法案検索結果
        </h2>
        <p className="text-gray-600">
          {total}件の法案が見つかりました
        </p>
      </div>

      {/* 法案一覧 */}
      <div className="space-y-6">
        {bills.map((bill, index) => (
          <div
            key={`${bill.bill_number}-${index}`}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            {/* 法案番号・タイトル */}
            <div className="mb-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="text-sm text-gray-500 mb-1">
                    {bill.bill_number} | 第{bill.session_number}回国会
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {bill.title}
                  </h3>
                </div>
                <a
                  href={bill.detail_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-4 text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
                >
                  詳細
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>

            {/* メタ情報 */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-4">
              {/* 提出者 */}
              <div className="flex items-center gap-1">
                <User className="h-4 w-4" />
                <span>{bill.submitter}</span>
              </div>

              {/* ステータス */}
              <div className="flex items-center gap-1">
                <Tag className="h-4 w-4" />
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bill.status_normalized)}`}>
                  {getStatusText(bill.status_normalized, bill.status)}
                </span>
              </div>

              {/* 委員会 */}
              {bill.committee && (
                <div className="flex items-center gap-1">
                  <Building className="h-4 w-4" />
                  <span>{bill.committee}</span>
                </div>
              )}

              {/* 提出日 */}
              {bill.submission_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDate(bill.submission_date)}</span>
                </div>
              )}
            </div>

            {/* 概要 */}
            {bill.summary && (
              <div className="mb-4">
                <div className="flex items-center gap-1 mb-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">概要</span>
                </div>
                <p className="text-gray-700 text-sm leading-relaxed">
                  {bill.summary.length > 300 
                    ? `${bill.summary.substring(0, 300)}...` 
                    : bill.summary
                  }
                </p>
              </div>
            )}

            {/* 関連リンク */}
            {bill.related_urls && bill.related_urls.length > 0 && (
              <div className="mb-4">
                <div className="text-sm font-medium text-gray-700 mb-2">関連資料</div>
                <div className="space-y-1">
                  {bill.related_urls.slice(0, 3).map((link, linkIndex) => (
                    <a
                      key={linkIndex}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      {link.title || '関連資料'}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* フッター情報 */}
            <div className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t border-gray-100">
              <span>
                出典: 衆議院法案データベース
              </span>
              <span>
                収集日: {formatDate(bill.collected_at.split('T')[0])}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* ページング情報 */}
      {total > bills.length && (
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            {bills.length}件 / {total}件を表示中
          </p>
        </div>
      )}
    </div>
  );
}