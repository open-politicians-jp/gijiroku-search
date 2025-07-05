'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, ExternalLink, Users, Calendar, FileText, BookOpen, Target, DollarSign, Heart, Shield, Building } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';

interface ManifestoDetail {
  party: string;
  title: string;
  year: number;
  url: string;
  sections: {
    title: string;
    icon: React.ComponentType<any>;
    content: string[];
    keyPoints: string[];
  }[];
  summary: {
    main_theme: string;
    target_voters: string;
    key_policies: string[];
    priorities: string[];
  };
}

export default function RikkenminshutoManifestoPage() {
  const [manifesto] = useState<ManifestoDetail>({
    party: '立憲民主党',
    title: '2025年参議院選挙ビジョン',
    year: 2025,
    url: 'https://cdp-japan.jp/election2025/visions/',
    sections: [
      {
        title: '格差解消',
        icon: Heart,
        content: [
          '最低賃金の大幅引き上げ',
          '非正規雇用の処遇改善',
          '税制の累進性強化',
          '社会保障制度の充実'
        ],
        keyPoints: [
          '最低賃金1500円を目指す',
          '同一労働同一賃金の徹底',
          '富裕層への課税強化'
        ]
      },
      {
        title: '民主主義の強化',
        icon: BookOpen,
        content: [
          '政治の透明性向上',
          '情報公開の徹底',
          '国会の機能強化',
          '市民参加の促進'
        ],
        keyPoints: [
          '政治資金の完全公開',
          '官邸主導政治の見直し',
          '国会の審議時間確保'
        ]
      },
      {
        title: '平和・人権',
        icon: Shield,
        content: [
          '平和憲法の理念堅持',
          '専守防衛の徹底',
          '人権の尊重',
          '多様性の尊重'
        ],
        keyPoints: [
          '憲法9条の堅持',
          '自衛隊の海外派遣慎重化',
          'LGBTQ+の権利保護'
        ]
      },
      {
        title: '環境・エネルギー',
        icon: Target,
        content: [
          '原発ゼロ社会の実現',
          '再生可能エネルギーの拡大',
          '脱炭素社会の構築',
          'グリーンニューディール'
        ],
        keyPoints: [
          '2030年原発ゼロ',
          '再エネ比率50%以上',
          '脱炭素投資の拡大'
        ]
      }
    ],
    summary: {
      main_theme: '格差解消と民主主義の強化',
      target_voters: '働く世代・若者',
      key_policies: [
        '格差是正',
        '民主主義改革',
        '平和・人権',
        '脱原発'
      ],
      priorities: [
        '格差解消',
        '民主主義の強化',
        '平和・人権',
        '環境・エネルギー'
      ]
    }
  });

  return (
    <>
      <Header currentPage="manifestos" />
      <div className="container mx-auto px-4 py-8 mt-16">
        {/* 戻るボタン */}
        <div className="mb-6">
          <Link
            href="/manifestos"
            className="inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            マニフェスト一覧に戻る
          </Link>
        </div>

        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {manifesto.party} マニフェスト詳細
              </h1>
              <p className="text-gray-600 mb-4">{manifesto.title}</p>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {manifesto.year}年
                </span>
                <span className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  有権者向け要約版
                </span>
              </div>
            </div>
            <div className="ml-6">
              <a
                href={manifesto.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                原文を確認
                <ExternalLink className="h-4 w-4 ml-2" />
              </a>
            </div>
          </div>
        </div>

        {/* サマリー */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">政策の概要</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">基本テーマ</h3>
              <p className="text-gray-900 mb-4">{manifesto.summary.main_theme}</p>
              
              <h3 className="text-sm font-semibold text-gray-700 mb-2">想定する支持層</h3>
              <p className="text-gray-900">{manifesto.summary.target_voters}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">重点政策</h3>
              <ul className="space-y-2">
                {manifesto.summary.key_policies.map((policy, index) => (
                  <li key={index} className="flex items-center text-gray-900">
                    <Target className="h-4 w-4 text-blue-600 mr-2" />
                    {policy}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* 政策詳細 */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900">政策詳細</h2>
          
          {manifesto.sections.map((section, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center mb-4">
                <section.icon className="h-6 w-6 text-blue-600 mr-3" />
                <h3 className="text-xl font-semibold text-gray-900">{section.title}</h3>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">政策内容</h4>
                  <ul className="space-y-2">
                    {section.content.map((item, itemIndex) => (
                      <li key={itemIndex} className="flex items-start text-gray-700">
                        <span className="inline-block w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">重要ポイント</h4>
                  <ul className="space-y-2">
                    {section.keyPoints.map((point, pointIndex) => (
                      <li key={pointIndex} className="flex items-start text-gray-700">
                        <Target className="h-4 w-4 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 text-center">
            この要約は公開されているマニフェストを基に作成されています。
            詳細な政策内容については、必ず原文をご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}