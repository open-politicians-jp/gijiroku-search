'use client';

import { useState } from 'react';
import { ArrowLeft, FileText, Target, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
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

// 2026年衆議院選向け政策対比データ
const POLICY_COMPARISONS: PolicyComparison[] = [
  {
    theme: '消費税',
    parties: {
      '自民党': { stance: '△', detail: '現状維持' },
      '中道改革連合': { stance: '△', detail: '食料品の税率軽減・軽減税率維持' },
      '日本維新の会': { stance: '○', detail: '消費税・法人税の減税' },
      '日本共産党': { stance: '○', detail: '5%に緊急減税' },
      '国民民主党': { stance: '○', detail: '5%に引下げ（実質賃金プラスまで）' },
      'れいわ新選組': { stance: '○', detail: '消費税廃止' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '所得税減税',
    parties: {
      '自民党': { stance: '○', detail: '物価上昇に合わせ控除引上げ' },
      '中道改革連合': { stance: '△', detail: '給付付き税額控除・控除引上げ' },
      '日本維新の会': { stance: '○', detail: '減税による可処分所得増加' },
      '日本共産党': { stance: '△', detail: '富裕層・大企業は増税' },
      '国民民主党': { stance: '○', detail: '基礎控除等を178万円に' },
      'れいわ新選組': { stance: '○', detail: '積極財政による減税' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '賃上げ',
    parties: {
      '自民党': { stance: '○', detail: '持続的な賃上げ実現' },
      '中道改革連合': { stance: '○', detail: '物価高に負けない賃上げ・最低賃金1,500円へ' },
      '日本維新の会': { stance: '○', detail: '賃上げと社会保障改革' },
      '日本共産党': { stance: '○', detail: '最低賃金1500円、1700円目標' },
      '国民民主党': { stance: '○', detail: '給料が上がる経済を実現' },
      'れいわ新選組': { stance: '○', detail: '最低賃金1500円以上' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '物価高対策',
    parties: {
      '自民党': { stance: '○', detail: '給付金、ガソリン価格抑制' },
      '中道改革連合': { stance: '○', detail: '給付金、ガソリン価格引下げ・電気ガス料金軽減' },
      '日本維新の会': { stance: '○', detail: '社会保険料軽減で手取り増' },
      '日本共産党': { stance: '○', detail: '暮らし優先の政治に変える' },
      '国民民主党': { stance: '○', detail: 'ガソリン・電気代値下げ' },
      'れいわ新選組': { stance: '○', detail: '積極財政で物価高対策' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '子育て支援',
    parties: {
      '自民党': { stance: '○', detail: '高校授業料実質無償化' },
      '中道改革連合': { stance: '○', detail: '子育て環境整備・妊娠出産無償化・教育費負担軽減' },
      '日本維新の会': { stance: '○', detail: '教育無償化' },
      '日本共産党': { stance: '○', detail: '大学まで無償化目標' },
      '国民民主党': { stance: '○', detail: '高校まで教育費完全無償化' },
      'れいわ新選組': { stance: '○', detail: '子育て・教育の完全無償化' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '年金・社会保障',
    parties: {
      '自民党': { stance: '○', detail: '制度の充実' },
      '中道改革連合': { stance: '○', detail: '年金・給付水準の底上げ' },
      '日本維新の会': { stance: '○', detail: '社会保険料を下げる改革' },
      '日本共産党': { stance: '○', detail: '減らない年金へ' },
      '国民民主党': { stance: '○', detail: '最低保障機能強化' },
      'れいわ新選組': { stance: '○', detail: '社会保障の充実' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '憲法改正',
    parties: {
      '自民党': { stance: '○', detail: '改憲を目指す' },
      '中道改革連合': { stance: '△', detail: '慎重姿勢・9条1,2項堅持、加憲は検討' },
      '日本維新の会': { stance: '○', detail: '憲法改正原案を発表' },
      '日本共産党': { stance: '✕', detail: '9条改憲反対' },
      '国民民主党': { stance: '○', detail: '緊急事態対応で改正' },
      'れいわ新選組': { stance: '✕', detail: '現行憲法の尊重' },
      '参政党': { stance: '○', detail: '新日本憲法（構想案）' }
    }
  },
  {
    theme: '安全保障',
    parties: {
      '自民党': { stance: '○', detail: '総合的な安全保障体制確立' },
      '中道改革連合': { stance: '△', detail: '平和・外交重視、平和創出ビジョン' },
      '日本維新の会': { stance: '○', detail: '現実的な安全保障政策' },
      '日本共産党': { stance: '✕', detail: '軍拡路線反対' },
      '国民民主党': { stance: '○', detail: '自分の国は自分で守る' },
      'れいわ新選組': { stance: '△', detail: '外交重視' },
      '参政党': { stance: '○', detail: '国のまもり' }
    }
  },
  {
    theme: 'エネルギー・原発',
    parties: {
      '自民党': { stance: '○', detail: '原発活用、2050年ネットゼロ' },
      '中道改革連合': { stance: '△', detail: '再エネ推進・原発依存低減、安定供給' },
      '日本維新の会': { stance: '○', detail: '原発活用含むエネルギー政策' },
      '日本共産党': { stance: '○', detail: '脱原発、再エネ100%' },
      '国民民主党': { stance: '○', detail: '再エネ賦課金徴収停止' },
      'れいわ新選組': { stance: '○', detail: '脱原発、グリーン・ニューディール' },
      '参政党': { stance: '△', detail: '言及なし' }
    }
  },
  {
    theme: '政治改革',
    parties: {
      '自民党': { stance: '△', detail: '政治資金規正法改正' },
      '中道改革連合': { stance: '○', detail: '政治とカネの問題解決・政治改革の推進' },
      '日本維新の会': { stance: '○', detail: '維新版政治改革大綱' },
      '日本共産党': { stance: '○', detail: '企業団体献金禁止' },
      '国民民主党': { stance: '○', detail: '政治改革推進' },
      'れいわ新選組': { stance: '○', detail: '政治改革' },
      '参政党': { stance: '○', detail: '政治改革' }
    }
  },
  {
    theme: '外国人・移民',
    parties: {
      '自民党': { stance: '○', detail: '「違法外国人ゼロ」へ' },
      '中道改革連合': { stance: '△', detail: '人権に配慮した入管政策' },
      '日本維新の会': { stance: '△', detail: '適切な入管政策' },
      '日本共産党': { stance: '△', detail: '外国人の人権保護' },
      '国民民主党': { stance: '△', detail: '言及なし' },
      'れいわ新選組': { stance: '△', detail: '共生・人権' },
      '参政党': { stance: '○', detail: '移民政策の見直し' }
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

export default function ShugiinComparisonPage() {
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [selectedParties, setSelectedParties] = useState<string[]>([]);

  const allParties = ['自民党', '中道改革連合', '日本維新の会', '日本共産党', '国民民主党', 'れいわ新選組', '参政党'];
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
            2026年衆院選 政策対比表
          </h1>
          <p className="text-gray-600 mb-4">
            主要政党の政策スタンスを一覧で比較できます。各政策テーマをクリックすると詳細が表示されます。
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <FileText className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-700">
                <p className="font-semibold mb-1">政策対比について</p>
                <p>各政党の公式マニフェストや政策文書を基に、主要な政策を比較しています。必ず各政党の公式な情報を直接ご確認ください。</p>
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
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

        {/* 政策対比表 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full table-auto" style={{ minWidth: `${Math.max(600, 120 + (POLICY_COMPARISONS.length * 90))}px` }}>
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-200 sticky left-0 bg-gray-50 z-10 w-24 min-w-[96px]">
                    政党
                  </th>
                  {POLICY_COMPARISONS.map((comparison) => (
                    <th
                      key={comparison.theme}
                      className={`px-2 py-3 text-center text-xs font-semibold border-b border-gray-200 w-20 min-w-[80px] whitespace-nowrap cursor-pointer transition-colors hover:bg-blue-100 ${
                        selectedTheme === comparison.theme
                          ? 'bg-blue-200 text-blue-900'
                          : 'text-gray-900 hover:text-blue-700'
                      }`}
                      onClick={(e) => handleThemeClick(comparison.theme, e)}
                      onTouchStart={(e) => e.currentTarget.classList.add('bg-blue-200')}
                      onTouchEnd={(e) => e.currentTarget.classList.remove('bg-blue-200')}
                      style={{ touchAction: 'manipulation' }}
                      title={`${comparison.theme}の詳細を表示`}
                    >
                      {comparison.theme}
                      {selectedTheme === comparison.theme && (
                        <div className="text-xs mt-1">▼</div>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {parties.map((party, index) => (
                  <tr
                    key={party}
                    className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50 transition-colors`}
                  >
                    <td className="px-3 py-3 text-sm font-medium text-gray-900 border-b border-gray-200 sticky left-0 bg-inherit z-10 w-24 min-w-[96px]">
                      <div className="truncate" title={party}>
                        {party}
                      </div>
                    </td>
                    {POLICY_COMPARISONS.map((comparison) => (
                      <td key={comparison.theme} className="px-2 py-3 text-center border-b border-gray-200 w-20 min-w-[80px]">
                        <div className="flex items-center justify-center">
                          {getStanceIcon(comparison.parties[party]?.stance || '-')}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 凡例 */}
          <div className="p-4 bg-gray-50 border-t">
            <div className="mb-3">
              <div className="text-xs text-gray-600 mb-2 font-medium">凡例:</div>
              <div className="flex flex-wrap gap-3 text-xs">
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
            <div className="text-sm text-gray-600">
              政策項目をクリックで詳細表示 | 横スクロールで全ての政策を確認
            </div>
          </div>
        </div>

        {/* 選択された政策の詳細表示 */}
        {selectedTheme && (
          <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedTheme} - 各政党の詳細スタンス
              </h3>
              <button
                onClick={() => setSelectedTheme(null)}
                className="text-gray-400 hover:text-gray-600 p-1 rounded"
                aria-label="詳細を閉じる"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
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
          </div>
        )}

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">政策対比表について</h3>
          <p className="text-sm text-gray-600 mb-2">
            この対比表は各政党の公式マニフェストや政策文書を基に作成されています。
            政策の詳細や正確な内容については、必ず各政党の公式サイトをご確認ください。
          </p>
          <p className="text-xs text-gray-500">
            ※ 政策対比は参考情報として提供されています。投票の際は公式情報を必ずご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}
