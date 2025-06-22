export interface Legislator {
  id: string;
  name: string;
  house: 'shugiin' | 'sangiin'; // 衆議院 | 参議院
  party: string;
  constituency: string;
  electionYear: number;
  status: 'active' | 'inactive'; // 現職 | 非現職
  region?: string; // 地域（比例代表の場合）
  // 基本追加フィールド
  termCount?: number; // 当選回数
  termEnd?: string; // 任期満了日
  positions?: string; // 現在の役職
  profileUrl?: string; // 公式プロフィールURL
  photoUrl?: string; // 写真URL
  // 詳細情報フィールド (Issue #19対応)
  wikipediaUrl?: string; // Wikipedia URL
  wikipediaTitle?: string; // Wikipedia タイトル
  wikipediaSummary?: string; // Wikipedia 要約
  personalWebsite?: string; // 個人ウェブサイト URL
  personalWebsiteTitle?: string; // 個人ウェブサイト タイトル
  snsAccounts?: { [platform: string]: { url: string; username: string; text: string } }; // SNS アカウント
  openpoliticsUrl?: string; // OpenPolitics URL
  detailsEnhancedAt?: string; // 詳細強化日時
  otherLinks?: Array<{ url: string; title: string; type: string }>; // その他のリンク
}

export interface LegislatorFilter {
  house?: 'shugiin' | 'sangiin' | 'all';
  party?: string;
  search?: string;
  status?: 'active' | 'inactive' | 'all';
}

export interface LegislatorsData {
  metadata: {
    total_count: number;
    last_updated: string;
    data_source: string;
    sangiin_count?: number;
    shugiin_count?: number;
  };
  data: Legislator[];
}

export const HOUSE_LABELS = {
  shugiin: '衆議院',
  sangiin: '参議院',
} as const;

export const STATUS_LABELS = {
  active: '現職',
  inactive: '非現職',
} as const;