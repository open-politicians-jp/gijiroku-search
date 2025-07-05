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

export default function KomeitoManifestoPage() {
  const [manifesto] = useState<ManifestoDetail>({
    party: '公明党',
    title: '2025年参議院選挙マニフェスト',
    year: 2025,
    url: 'https://www.komei.or.jp/content/manifesto2025_02/',
    sections: [
      {
        title: '福祉・社会保障',
        icon: Heart,
        content: [
          '子育て支援の拡充',
          '高齢者・障がい者支援',
          '医療・介護制度の充実',
          '生活困窮者への支援強化'
        ],
        keyPoints: [
          '児童手当の拡充',
          '介護保険料の軽減',
          '医療費負担の軽減'
        ]
      },
      {
        title: '教育・人材育成',
        icon: BookOpen,
        content: [
          '教育費負担の軽減',
          '学校教育の質的向上',
          '生涯学習社会の実現',
          'デジタル人材の育成'
        ],
        keyPoints: [
          '高等教育の無償化拡大',
          '教員の働き方改革',
          'ICT教育の推進'
        ]
      },
      {
        title: '平和・外交',
        icon: Shield,
        content: [
          '平和外交の推進',
          '人道支援の拡充',
          '核軍縮・不拡散への取り組み',
          '国際協力の強化'
        ],
        keyPoints: [
          '平和構築への積極的関与',
          '人道支援予算の拡充',
          '核兵器廃絶への取り組み'
        ]
      },
      {
        title: '環境・エネルギー',
        icon: Target,
        content: [
          'カーボンニュートラルの実現',
          '再生可能エネルギーの普及',
          '循環型社会の構築',
          '環境技術の開発・普及'
        ],
        keyPoints: [
          '2050年カーボンニュートラル',
          '再エネ導入目標の達成',
          '脱炭素技術の開発支援'
        ]
      }
    ],
    summary: {
      main_theme: '福祉と平和を重視した政治',
      target_voters: '子育て世代・高齢者',
      key_policies: [
        '福祉制度の拡充',
        '教育支援',
        '平和外交',
        '環境政策'
      ],
      priorities: [
        '福祉・社会保障',
        '教育・人材育成',
        '平和・外交',
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
        <div className="bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-lg p-6 mb-8">
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
                className="inline-flex items-center px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
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
                    <Target className="h-4 w-4 text-yellow-600 mr-2" />
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
                <section.icon className="h-6 w-6 text-yellow-600 mr-3" />
                <h3 className="text-xl font-semibold text-gray-900">{section.title}</h3>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">政策内容</h4>
                  <ul className="space-y-2">
                    {section.content.map((item, itemIndex) => (
                      <li key={itemIndex} className="flex items-start text-gray-700">
                        <span className="inline-block w-2 h-2 bg-yellow-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
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