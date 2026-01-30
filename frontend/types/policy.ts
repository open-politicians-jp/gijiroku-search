// 政策関連の型定義

/**
 * 個別の政策項目
 */
export interface PolicyItem {
  /** 政策のタイトル */
  title: string;
  /** 政策の詳細説明 */
  description: string;
  /** 参考URL一覧 */
  references?: PolicyReference[];
}

/**
 * 政策参考情報
 */
export interface PolicyReference {
  /** 参考URL */
  url: string;
  /** URL説明 */
  description: string;
  /** 出典タイプ */
  source_type: 'official' | 'gemini_search' | 'news' | 'other';
  /** 信頼度 */
  reliability: 'high' | 'medium' | 'low';
}

/**
 * 政策カテゴリ
 */
export interface PolicyCategory {
  /** カテゴリ名 */
  category: string;
  /** カテゴリ内の政策一覧 */
  policies: PolicyItem[];
}

/**
 * 政党の政策情報
 */
export interface PartyPolicy {
  /** 政党名 */
  name: string;
  /** 基本テーマ（LLM要約） */
  basic_theme?: string;
  /** 想定支持層（LLM要約） */
  target_voters?: string[];
  /** 重点政策（LLM要約） */
  key_policies?: string[];
  /** 政策カテゴリ一覧 */
  categories: PolicyCategory[];
  /** 政党レベルの参考URL一覧 */
  party_references?: PolicyReference[];
  /** 公式サイトURL */
  official_url?: string;
}

/**
 * 政策要約データ全体
 */
export interface PolicySummaryData {
  /** データ生成日時 */
  generated_at: string;
  /** データの説明 */
  description: string;
  /** 政党一覧 */
  parties: PartyPolicy[];
  /** 利用可能なカテゴリ一覧 */
  categories?: string[];
  /** 総政党数 */
  total_parties: number;
  /** データソース */
  data_source?: string;
  /** URL参照情報の有無 */
  has_url_references?: boolean;
  /** 選挙種別 (shugiin/sangiin) */
  election_type?: string;
  /** 選挙年 */
  election_year?: number;
}

/**
 * 政策検索結果
 */
export interface PolicySearchResult {
  /** 政党名 */
  partyName: string;
  /** カテゴリ名 */
  categoryName: string;
  /** 政策項目 */
  policy: PolicyItem;
  /** 検索マッチ度（0-1） */
  relevance?: number;
}

/**
 * 政策比較データ
 */
export interface PolicyComparison {
  /** 比較対象の政党名一覧 */
  partyNames: string[];
  /** カテゴリ名 */
  categoryName: string;
  /** 各政党の該当カテゴリの政策一覧 */
  policies: { [partyName: string]: PolicyItem[] };
}

/**
 * 政策フィルター条件
 */
export interface PolicyFilter {
  /** 政党名で絞り込み */
  partyNames?: string[];
  /** カテゴリで絞り込み */
  categories?: string[];
  /** キーワード検索 */
  keyword?: string;
}

/**
 * 政策統計情報
 */
export interface PolicyStats {
  /** 政党別政策数 */
  policiesByParty: { [partyName: string]: number };
  /** カテゴリ別政策数 */
  policiesByCategory: { [categoryName: string]: number };
  /** 総政策数 */
  totalPolicies: number;
  /** 最も多い政策カテゴリ */
  mostCommonCategory: string;
  /** 最も政策数の多い政党 */
  mostActivePart: string;
}

/**
 * 政策キーワード分析結果
 */
export interface PolicyKeywordAnalysis {
  /** キーワード */
  keyword: string;
  /** 出現回数 */
  frequency: number;
  /** 該当政党名一覧 */
  parties: string[];
  /** 該当カテゴリ一覧 */
  categories: string[];
}

/**
 * 政策トレンド分析
 */
export interface PolicyTrend {
  /** トレンドキーワード */
  keyword: string;
  /** 言及している政党数 */
  partyCount: number;
  /** 言及している政党名一覧 */
  parties: string[];
  /** トレンドスコア（0-1） */
  trendScore: number;
}

/**
 * 政策詳細ページ用データ
 */
export interface PolicyDetailData {
  /** 政党情報 */
  party: PartyPolicy;
  /** 関連政党（類似政策を持つ政党） */
  relatedParties: PartyPolicy[];
  /** 政策統計 */
  stats: PolicyStats;
}

/**
 * API レスポンス型
 */
export interface PolicyApiResponse<T = any> {
  /** 成功フラグ */
  success: boolean;
  /** データ */
  data: T;
  /** エラーメッセージ */
  error?: string;
  /** メタデータ */
  meta?: {
    /** 総件数 */
    total: number;
    /** ページネーション情報 */
    pagination?: {
      page: number;
      limit: number;
      totalPages: number;
    };
  };
}