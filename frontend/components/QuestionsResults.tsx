'use client';

import { ExternalLink, Calendar, Building, Tag, FileText, User, MessageSquare } from 'lucide-react';
import SpeakerLink from './SpeakerLink';

interface Question {
  title: string;
  question_number: string;
  questioner: string;
  house: string;
  submission_date: string;
  answer_date: string;
  question_content: string;
  answer_content: string;
  question_url: string;
  answer_url: string;
  category: string;
  collected_at: string;
  year: number;
  week: number;
}

interface QuestionsResultsProps {
  questions: Question[];
  total: number;
  loading?: boolean;
}

export default function QuestionsResults({ questions, total, loading = false }: QuestionsResultsProps) {
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-3"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/4 mb-2"></div>
              <div className="h-16 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-16 bg-gray-200 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 text-center py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <p className="text-gray-500">検索条件に一致する質問主意書が見つかりませんでした。</p>
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

  const getCategoryColor = (category: string) => {
    const categoryColors: Record<string, string> = {
      '内政': 'bg-blue-100 text-blue-800',
      '外交': 'bg-green-100 text-green-800',
      '経済': 'bg-yellow-100 text-yellow-800',
      '社会保障': 'bg-purple-100 text-purple-800',
      '教育': 'bg-indigo-100 text-indigo-800',
      '環境': 'bg-emerald-100 text-emerald-800',
      '労働': 'bg-orange-100 text-orange-800',
      '防衛': 'bg-red-100 text-red-800',
      '司法': 'bg-gray-100 text-gray-800',
      '地方': 'bg-pink-100 text-pink-800'
    };
    
    return categoryColors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      {/* 検索結果ヘッダー */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          質問主意書検索結果
        </h2>
        <p className="text-gray-600">
          {total}件の質問主意書が見つかりました
        </p>
      </div>

      {/* 質問主意書一覧 */}
      <div className="space-y-6">
        {questions.map((question, index) => (
          <div
            key={`${question.question_number}-${index}`}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            {/* ヘッダー情報 */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                  <span>第{question.question_number}号</span>
                  <span>•</span>
                  <span>{question.house}</span>
                  {question.submission_date && (
                    <>
                      <span>•</span>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(question.submission_date)}</span>
                      </div>
                    </>
                  )}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {question.title}
                </h3>
              </div>
              {question.question_url && (
                <a
                  href={question.question_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-4 text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
                >
                  質問書
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>

            {/* メタ情報 */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-4">
              {/* 質問者 */}
              <div className="flex items-center gap-1">
                <User className="h-4 w-4" />
                <SpeakerLink 
                  speakerName={question.questioner} 
                  className="text-gray-900 font-medium"
                />
              </div>

              {/* カテゴリ */}
              <div className="flex items-center gap-1">
                <Tag className="h-4 w-4" />
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(question.category)}`}>
                  {question.category}
                </span>
              </div>

              {/* 院 */}
              <div className="flex items-center gap-1">
                <Building className="h-4 w-4" />
                <span>{question.house}</span>
              </div>
            </div>

            {/* 質問内容 */}
            {question.question_content && (
              <div className="mb-4">
                <div className="flex items-center gap-1 mb-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">質問内容</span>
                </div>
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {question.question_content.length > 300 
                      ? `${question.question_content.substring(0, 300)}...` 
                      : question.question_content
                    }
                  </p>
                </div>
              </div>
            )}

            {/* 答弁内容 */}
            {question.answer_content && (
              <div className="mb-4">
                <div className="flex items-center gap-1 mb-2">
                  <MessageSquare className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">政府答弁</span>
                  {question.answer_url && (
                    <a
                      href={question.answer_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-blue-600 hover:text-blue-700 flex items-center gap-1 text-xs"
                    >
                      答弁書
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {question.answer_content.length > 300 
                      ? `${question.answer_content.substring(0, 300)}...` 
                      : question.answer_content
                    }
                  </p>
                </div>
              </div>
            )}

            {/* フッター情報 */}
            <div className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t border-gray-100">
              <span>
                出典: 国会質問主意書データベース
              </span>
              <span>
                収集日: {formatDate(question.collected_at.split('T')[0])}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* ページング情報 */}
      {total > questions.length && (
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            {questions.length}件 / {total}件を表示中
          </p>
        </div>
      )}
    </div>
  );
}