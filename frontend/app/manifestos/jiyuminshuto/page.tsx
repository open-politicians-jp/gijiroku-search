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

export default function JiyuminshutoManifestoPage() {
  const [manifesto] = useState<ManifestoDetail>({
    party: '自由民主党',
    title: '令和7年参議院選挙公約',
    year: 2025,
    url: 'https://storage2.jimin.jp/pdf/pamphlet/202507_manifest.pdf',
    sections: [
      {
        title: '経済政策',
        icon: DollarSign,
        content: [
          '経済成長を最優先とした政策展開',
          '企業の投資促進と新産業創出',
          '地方経済の活性化と雇用創出',
          'デジタル化推進による生産性向上'
        ],
        keyPoints: [
          '実質GDP成長率2%以上を目指す',
          '法人税減税による企業投資促進',
          '地方創生総合戦略の拡充'
        ]
      },
      {
        title: '社会保障',
        icon: Heart,
        content: [
          '全世代型社会保障制度の構築',
          '医療・介護サービスの充実',
          '子育て支援の拡充',
          '高齢者の生活支援強化'
        ],
        keyPoints: [
          '子育て給付金の拡充',
          '介護人材の確保と処遇改善',
          '医療DXの推進'
        ]
      },
      {
        title: '安全保障',
        icon: Shield,
        content: [
          '防衛力の抜本的強化',
          '日米同盟の深化',
          '自由で開かれたインド太平洋の実現',
          '経済安全保障の強化'
        ],
        keyPoints: [
          '防衛費GDP比2%達成',
          '反撃能力の整備',
          '情報収集・分析能力の向上'
        ]
      },
      {
        title: '地方創生',
        icon: Building,
        content: [
          '東京一極集中の是正',
          '地方移住・定住の促進',
          '地域産業の振興',
          'デジタル田園都市国家構想の推進'
        ],
        keyPoints: [
          '地方移住支援金の拡充',
          'テレワーク環境整備',
          '地域の特色を活かした産業振興'
        ]
      }
    ],
    summary: {
      main_theme: '経済成長と安全保障の両立',
      target_voters: '幅広い世代の国民',
      key_policies: [
        '経済成長重視の政策',
        '防衛力強化',
        '全世代型社会保障',
        '地方創生'
      ],
      priorities: [
        '経済政策',
        '安全保障',
        '社会保障',
        '地方創生'
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
        <div className="bg-gradient-to-r from-red-50 to-red-100 rounded-lg p-6 mb-8">
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
                className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
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
                    <Target className="h-4 w-4 text-red-600 mr-2" />
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
                <section.icon className="h-6 w-6 text-red-600 mr-3" />
                <h3 className="text-xl font-semibold text-gray-900">{section.title}</h3>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">政策内容</h4>
                  <ul className="space-y-2">
                    {section.content.map((item, itemIndex) => (
                      <li key={itemIndex} className="flex items-start text-gray-700">
                        <span className="inline-block w-2 h-2 bg-red-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
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