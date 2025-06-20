export interface Legislator {
  id: string;
  name: string;
  house: 'shugiin' | 'sangiin'; // 衆議院 | 参議院
  party: string;
  constituency: string;
  electionYear: number;
  status: 'active' | 'inactive'; // 現職 | 非現職
  region?: string; // 地域（比例代表の場合）
  // 追加フィールド（実際のデータ用）
  termCount?: number; // 当選回数
  termEnd?: string; // 任期満了日
  positions?: string; // 現在の役職
  profileUrl?: string; // 公式プロフィールURL
  photoUrl?: string; // 写真URL
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