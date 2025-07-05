'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, FileText, Target, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';

interface PolicyComparison {
  theme: string;
  parties: {
    [party: string]: {
      stance: '○' | '△' | '✕' | '-';
      detail: string;
    }
  }
}

// 最新のoutput/summary.mdから取得した対比表データ
const POLICY_COMPARISONS: PolicyComparison[] = [
  {
    theme: '消費税',
    parties: {
      '自民党': { stance: '△', detail: '現状維持・言及なし' },
      '立憲民主党': { stance: '○', detail: '食料品0%' },
      '公明党': { stance: '△', detail: '軽減税率維持' },
      '日本共産党': { stance: '○', detail: '5%に緊急減税' },
      '国民民主党': { stance: '○', detail: '5%に（実質賃金プラスまで）' },
      'れいわ新選組': { stance: '-', detail: '言及なし' },
      '日本保守党': { stance: '○', detail: '食料品0%' },
      '参政党': { stance: '△', detail: '言及なし' },
      'NHK党': { stance: '○', detail: '5%に恒久的に引下げ' },
      '日本改革党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '所得税減税',
    parties: {
      '自民党': { stance: '○', detail: '物価上昇に合わせ控除引上' },
      '立憲民主党': { stance: '△', detail: '言及なし' },
      '公明党': { stance: '○', detail: '控除の更なる引上げ' },
      '日本共産党': { stance: '△', detail: '富裕層・大企業は増税' },
      '国民民主党': { stance: '○', detail: '基礎控除等を178万円に' },
      'れいわ新選組': { stance: '-', detail: '言及なし' },
      '日本保守党': { stance: '○', detail: '控除額の引上げ' },
      '参政党': { stance: '△', detail: '言及なし' },
      'NHK党': { stance: '○', detail: '基礎控除200万円まで引上げ' },
      '日本改革党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '賃上げ',
    parties: {
      '自民党': { stance: '○', detail: '持続的な賃上げ実現' },
      '立憲民主党': { stance: '○', detail: '物価高に負けない賃上げ' },
      '公明党': { stance: '○', detail: '最低賃金1,500円へ' },
      '日本共産党': { stance: '○', detail: '最低賃金1500円、1700円目標' },
      '国民民主党': { stance: '○', detail: '給料が上がる経済を実現' },
      'れいわ新選組': { stance: '-', detail: '言及なし' },
      '日本保守党': { stance: '△', detail: '言及なし' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '物価高対策',
    parties: {
      '自民党': { stance: '○', detail: '給付金、ガソリン価格抑制' },
      '立憲民主党': { stance: '○', detail: '給付金、ガソリン価格引下' },
      '公明党': { stance: '○', detail: '給付金、電気・ガス料金軽減' },
      '日本共産党': { stance: '○', detail: '暮らし優先の政治に変える' },
      '国民民主党': { stance: '○', detail: 'ガソリン・電気代値下げ' },
      'れいわ新選組': { stance: '-', detail: '言及なし' },
      '日本保守党': { stance: '○', detail: 'ガソリン税減税' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '子育て支援',
    parties: {
      '自民党': { stance: '○', detail: '高校授業料実質無償化' },
      '立憲民主党': { stance: '○', detail: '子育てしやすい環境整備' },
      '公明党': { stance: '○', detail: '妊娠・出産無償化、教育費負担軽減' },
      '日本共産党': { stance: '○', detail: '大学まで無償化目標' },
      '国民民主党': { stance: '○', detail: '高校まで教育費完全無償化' },
      'れいわ新選組': { stance: '○', detail: '子育て・教育政策' },
      '日本保守党': { stance: '○', detail: '出産育児一時金引上（国籍条項付）' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '年金',
    parties: {
      '自民党': { stance: '○', detail: '制度の充実' },
      '立憲民主党': { stance: '○', detail: '年金の底上げ' },
      '公明党': { stance: '○', detail: '給付水準の底上げ' },
      '日本共産党': { stance: '○', detail: '減らない年金へ' },
      '国民民主党': { stance: '○', detail: '最低保障機能強化' },
      'れいわ新選組': { stance: '-', detail: '言及なし' },
      '日本保守党': { stance: '△', detail: '言及なし' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '憲法改正',
    parties: {
      '自民党': { stance: '○', detail: '改憲を目指す' },
      '立憲民主党': { stance: '△', detail: '言及なし' },
      '公明党': { stance: '△', detail: '9条1,2項は堅持、加憲は検討' },
      '日本共産党': { stance: '✕', detail: 'アメリカ言いなり政治を改める' },
      '国民民主党': { stance: '○', detail: '緊急事態対応で改正' },
      'れいわ新選組': { stance: '✕', detail: '現行憲法の尊重' },
      '日本保守党': { stance: '○', detail: '9条2項削除' },
      '参政党': { stance: '△', detail: '新日本憲法（構想案）' }
    }
  },
  {
    theme: '安全保障',
    parties: {
      '自民党': { stance: '○', detail: '総合的な安全保障体制確立' },
      '立憲民主党': { stance: '○', detail: '日本の平和を守る' },
      '公明党': { stance: '△', detail: '平和創出ビジョン' },
      '日本共産党': { stance: '✕', detail: 'アメリカ言いなり政治を改める' },
      '国民民主党': { stance: '○', detail: '自分の国は自分で守る' },
      'れいわ新選組': { stance: '○', detail: '外交・安全保障' },
      '日本保守党': { stance: '○', detail: '防衛力強化' },
      '参政党': { stance: '○', detail: '国のまもり' }
    }
  },
  {
    theme: 'エネルギー',
    parties: {
      '自民党': { stance: '○', detail: '2050年ネットゼロ' },
      '立憲民主党': { stance: '○', detail: '農山漁村・生活インフラを守る' },
      '公明党': { stance: '△', detail: '言及なし' },
      '日本共産党': { stance: '○', detail: '脱原発' },
      '国民民主党': { stance: '○', detail: '再エネ賦課金徴収停止' },
      'れいわ新選組': { stance: '○', detail: '脱原発' },
      '日本保守党': { stance: '○', detail: '再エネ賦課金廃止' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '外国人・移民',
    parties: {
      '自民党': { stance: '○', detail: '「違法外国人ゼロ」へ' },
      '立憲民主党': { stance: '△', detail: '言及なし' },
      '公明党': { stance: '△', detail: '言及なし' },
      '日本共産党': { stance: '△', detail: '言及なし' },
      '国民民主党': { stance: '△', detail: '言及なし' },
      'れいわ新選組': { stance: '-', detail: '言及なし' },
      '日本保守党': { stance: '○', detail: '移民政策の是正' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: 'ジェンダー/LGBT',
    parties: {
      '自民党': { stance: '△', detail: '女性活躍推進' },
      '立憲民主党': { stance: '○', detail: 'ジェンダー平等推進' },
      '公明党': { stance: '△', detail: '選択的夫婦別姓導入推進' },
      '日本共産党': { stance: '○', detail: 'ジェンダー平等' },
      '国民民主党': { stance: '△', detail: '言及なし' },
      'れいわ新選組': { stance: '○', detail: 'ジェンダー平等' },
      '日本保守党': { stance: '○', detail: 'LGBT法改正' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  }
];

const getStanceIcon = (stance: string) => {
  switch (stance) {
    case '○':
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    case '△':
      return <AlertCircle className="h-5 w-5 text-yellow-600" />;
    case '✕':
      return <XCircle className="h-5 w-5 text-red-600" />;
    default:
      return <span className="text-gray-400">-</span>;
  }
};

const getStanceColor = (stance: string) => {
  switch (stance) {
    case '○':
      return 'bg-green-50 border-green-200';
    case '△':
      return 'bg-yellow-50 border-yellow-200';
    case '✕':
      return 'bg-red-50 border-red-200';
    default:
      return 'bg-gray-50 border-gray-200';
  }
};

export default function SangiinComparisonPage() {
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [selectedParties, setSelectedParties] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const allParties = ['自民党', '立憲民主党', '公明党', '日本共産党', '国民民主党', 'れいわ新選組', '日本保守党', '参政党', 'NHK党', '日本改革党', '社会民主党'];
  const parties = selectedParties.length > 0 ? selectedParties : allParties;
  
  const handlePartyToggle = (party: string) => {
    setSelectedParties(prev => {
      if (prev.includes(party)) {
        return prev.filter(p => p !== party);
      } else {
        return [...prev, party];
      }
    });
  };

  const resetPartySelection = () => {
    setSelectedParties([]);
  };

  // スマートフォン対応：タッチイベント処理
  const handleThemeClick = (theme: string, event: React.MouseEvent | React.TouchEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedTheme(selectedTheme === theme ? null : theme);
  };

  return (
    <>
      <Header currentPage="manifestos" />
      <div className="container mx-auto px-4 py-8 mt-16">
        {/* ナビゲーション */}
        <div className="mb-6">
          <Link
            href="/manifestos"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            マニフェスト一覧に戻る
          </Link>
        </div>

        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4 flex items-center">
            <Target className="h-8 w-8 text-blue-600 mr-3" />
            参院選 政策対比表
          </h1>
          <p className="text-gray-600 mb-4">
            主要政党の政策スタンスを一覧で比較できます。各政策テーマをクリックすると詳細が表示されます。
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <FileText className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-700">
                <p className="font-semibold mb-1">政策対比について (Claude Code Sonnet4, Gemini 2.5 Pro による解析)</p>
                <p>各政党の公表情報に基づき、Claude Code Sonnet4、Gemini 2.5 Proが機械的な判断で主要な政策を比較しています。必ず各政党の公式な情報を直接ご確認ください。</p>
                <div className="flex items-center gap-4 mt-2 text-xs">
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    ○: 積極的
                  </span>
                  <span className="flex items-center gap-1">
                    <AlertCircle className="h-3 w-3 text-yellow-600" />
                    △: 部分的・条件付
                  </span>
                  <span className="flex items-center gap-1">
                    <XCircle className="h-3 w-3 text-red-600" />
                    ✕: 反対・消極的
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="text-gray-400">-</span>
                    : 言及なし
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 政党選択フィルター */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">表示政党の選択</h2>
          <p className="text-sm text-gray-600 mb-4">
            比較したい政党を選択してください。未選択の場合は全政党が表示されます。
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 mb-4">
            {allParties.map((party) => (
              <label key={party} className="flex items-center space-x-2 p-2 rounded border hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedParties.includes(party)}
                  onChange={() => handlePartyToggle(party)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-900">{party}</span>
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={resetPartySelection}
              className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              全て表示
            </button>
            <span className="text-sm text-gray-500 py-2">
              {selectedParties.length > 0 ? `${selectedParties.length}政党選択中` : '全政党表示中'}
            </span>
          </div>
        </div>

        {/* 政策対比表 - 新しいカード形式 */}
        <div className="space-y-4">
          {/* 政策テーマヘッダー */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">政策テーマを選択</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {POLICY_COMPARISONS.map((comparison) => (
                <button
                  key={comparison.theme}
                  onClick={(e) => handleThemeClick(comparison.theme, e)}
                  onTouchStart={(e) => e.currentTarget.classList.add('bg-blue-200')}
                  onTouchEnd={(e) => e.currentTarget.classList.remove('bg-blue-200')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    selectedTheme === comparison.theme
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 active:bg-blue-200'
                  }`}
                  style={{ touchAction: 'manipulation' }}
                >
                  {comparison.theme}
                </button>
              ))}
            </div>
            <div className="mt-3 text-sm text-gray-500">
              💡 政策テーマをタップすると各政党の詳細が表示されます
            </div>
          </div>

          {/* 選択されたテーマの対比表 */}
          {selectedTheme && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  📊 {selectedTheme} - 政党比較
                </h3>
                <button
                  onClick={() => setSelectedTheme(null)}
                  className="text-gray-400 hover:text-gray-600 p-1 rounded"
                  aria-label="比較を閉じる"
                >
                  ✕
                </button>
              </div>
              
              {/* 政党別スタンス表示 */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {parties
                  .filter(party => POLICY_COMPARISONS.find(c => c.theme === selectedTheme)?.parties[party])
                  .map((party) => {
                    const partyData = POLICY_COMPARISONS.find(c => c.theme === selectedTheme)?.parties[party];
                    if (!partyData) return null;
                    
                    return (
                      <div key={party} className={`border-2 rounded-lg p-3 ${getStanceColor(partyData.stance)}`}>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-gray-900 text-sm">{party}</h4>
                          <div className="flex items-center">
                            {getStanceIcon(partyData.stance)}
                          </div>
                        </div>
                        <p className="text-sm text-gray-700 leading-relaxed">{partyData.detail}</p>
                      </div>
                    );
                  })}
              </div>

              {/* 凡例 */}
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-600 mb-2 font-medium">凡例:</div>
                <div className="flex flex-wrap gap-4 text-xs">
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    <span>○: 積極的</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <AlertCircle className="h-3 w-3 text-yellow-600" />
                    <span>△: 部分的・条件付</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <XCircle className="h-3 w-3 text-red-600" />
                    <span>✕: 反対・消極的</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-gray-400">-</span>
                    <span>: 言及なし</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 初期状態のメッセージ */}
          {!selectedTheme && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
              <FileText className="h-12 w-12 text-blue-600 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                政策テーマを選択してください
              </h3>
              <p className="text-blue-700">
                上記のボタンから関心のある政策テーマを選択すると、各政党のスタンスを比較できます。
              </p>
            </div>
          )}
        </div>


        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">政策対比表について</h3>
          <p className="text-sm text-gray-600 mb-2">
            この対比表は各政党の公式マニフェストや政策文書をClaude Code Sonnet4、Gemini 2.5 Proが解析し作成されています。
            政策の詳細や正確な内容については、必ず各政党の公式サイトをご確認ください。
          </p>
          <p className="text-xs text-gray-500">
            ※ AI解析による政策対比は参考情報として提供されています。投票の際は公式情報を必ずご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}