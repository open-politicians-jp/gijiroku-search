export interface Legislator {
  id: string;
  name: string;
  house: 'shugiin' | 'sangiin'; // 衆議院 | 参議院
  party: string;
  constituency: string;
  electionYear: number;
  status: 'active' | 'inactive'; // 現職 | 非現職
  region?: string; // 地域（比例代表の場合）
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