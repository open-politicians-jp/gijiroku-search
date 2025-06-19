'use client';

import { Question } from '@/types';
import { Calendar, User, Users, Building, ExternalLink, FileText, Download } from 'lucide-react';
import { format, parseISO } from 'date-fns';

interface QuestionResultsProps {
  questions: Question[];
  total: number;
  loading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  currentOffset?: number;
  limit?: number;
}

export default function QuestionResults({ 
  questions, 
  total, 
  loading = false, 
  onLoadMore, 
  hasMore = false, 
  currentOffset = 0, 
  limit = 20 
}: QuestionResultsProps) {
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">検索中...</p>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <p className="text-gray-600 text-lg">検索結果が見つかりませんでした</p>
          <p className="text-gray-500 mt-2">検索条件を変更してお試しください</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), 'yyyy年MM月dd日');
    } catch {
      return dateString;
    }
  };

  const truncateText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const getHouseDisplay = (house: string) => {
    const houseMap: { [key: string]: string } = {
      '衆議院': '衆',
      '参議院': '参',
      'shugiin': '衆',
      'sangiin': '参'
    };
    return houseMap[house] || house;
  };

  const getCategoryBadgeColor = (category: string) => {
    const colorMap: { [key: string]: string } = {
      '外交・安全保障': 'bg-red-100 text-red-800',
      '内政・行政': 'bg-blue-100 text-blue-800',
      '経済・財政': 'bg-green-100 text-green-800',
      '社会保障': 'bg-purple-100 text-purple-800',
      '教育・文化': 'bg-yellow-100 text-yellow-800',
      '環境・エネルギー': 'bg-emerald-100 text-emerald-800',
      '司法・法務': 'bg-gray-100 text-gray-800',
      '地方・自治': 'bg-pink-100 text-pink-800',
      'IT・デジタル': 'bg-cyan-100 text-cyan-800',
      '国土・交通': 'bg-orange-100 text-orange-800',
      '一般': 'bg-gray-100 text-gray-600'
    };
    return colorMap[category] || 'bg-gray-100 text-gray-600';
  };

  return (
    <div className="max-w-4xl mx-auto mt-8">
      {/* 検索結果サマリー */}
      <div className="mb-6 text-sm text-gray-600">
        <span className="font-medium text-gray-900">{total.toLocaleString()}</span>件の質問主意書が見つかりました
      </div>

      {/* 検索結果リスト */}
      <div className="space-y-6">
        {questions.map((question) => (
          <div key={question.question_number} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            {/* ヘッダー情報 */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-4 mb-4">
              {/* 質問番号 */}
              <div className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                質問第{question.question_number}号
              </div>
              
              {/* カテゴリ */}
              {question.category && (
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getCategoryBadgeColor(question.category)}`}>
                  {question.category}
                </div>
              )}
              
              {/* 院 */}
              {question.house && (
                <div className="flex items-center gap-1 text-gray-600">
                  <Building className="h-4 w-4" />
                  <span className="text-sm">{getHouseDisplay(question.house)}</span>
                </div>
              )}
            </div>

            {/* タイトル */}
            <h3 className="text-lg font-medium text-gray-900 mb-3">
              {question.title}
            </h3>

            {/* 質問者・日付情報 */}
            <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600">
              {question.questioner && (
                <div className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  <span>質問者: {question.questioner}</span>
                </div>
              )}
              
              {question.submission_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>提出日: {formatDate(question.submission_date)}</span>
                </div>
              )}
              
              {question.answer_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>答弁日: {formatDate(question.answer_date)}</span>
                </div>
              )}
            </div>

            {/* 質問内容 */}
            {question.question_content && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">質問内容</h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {truncateText(question.question_content, 300)}
                  </p>
                </div>
              </div>
            )}

            {/* 答弁内容 */}
            {question.answer_content && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">政府答弁</h4>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {truncateText(question.answer_content, 300)}
                  </p>
                </div>
              </div>
            )}

            {/* リンク */}
            <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-100">
              {/* HTML リンク */}
              {question.question_url && (
                <a
                  href={question.question_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm"
                >
                  <FileText className="h-4 w-4" />
                  HTML版を見る
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}

              {/* 答弁URL */}
              {question.answer_url && question.answer_url !== question.question_url && (
                <a
                  href={question.answer_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm"
                >
                  <FileText className="h-4 w-4" />
                  答弁書を見る
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}

              {/* PDF リンク */}
              {question.pdf_links && question.pdf_links.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {question.pdf_links.map((pdf, index) => (
                    <a
                      key={index}
                      href={pdf.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors text-sm"
                    >
                      <Download className="h-4 w-4" />
                      {pdf.title || `PDF ${index + 1}`}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ))}
                </div>
              )}

              {/* HTML詳細リンク */}
              {question.html_links && question.html_links.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {question.html_links.map((html, index) => (
                    <a
                      key={index}
                      href={html.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors text-sm"
                    >
                      <FileText className="h-4 w-4" />
                      {html.title || `HTML ${index + 1}`}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ))}
                </div>
              )}
            </div>

            {/* フッター */}
            <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500">
              <span>収集日: {formatDate(question.collected_at)}</span>
              {question.year && question.week && (
                <span>{question.year}年 第{question.week}週</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 読み込みボタン */}
      {hasMore && onLoadMore && (
        <div className="text-center mt-8">
          <button
            onClick={onLoadMore}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '読み込み中...' : 'さらに読み込む'}
          </button>
          <p className="text-sm text-gray-500 mt-2">
            {currentOffset + questions.length} / {total} 件表示中
          </p>
        </div>
      )}
    </div>
  );
}