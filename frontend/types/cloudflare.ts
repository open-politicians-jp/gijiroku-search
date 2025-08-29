// Cloudflare D1データベース型定義

/// <reference types="@cloudflare/workers-types" />

export interface Env {
  DB: D1Database;
}

export interface D1PreparedStatement {
  bind(...values: any[]): D1PreparedStatement;
  first<T = unknown>(colName?: string): Promise<T | null>;
  run(): Promise<D1Result>;
  all<T = unknown>(): Promise<D1Result<T>>;
  raw<T = unknown>(): Promise<T[]>;
}

export interface D1Result<T = unknown> {
  results: T[];
  success: boolean;
  error?: string;
  meta: {
    changed_db: boolean;
    changes: number;
    duration: number;
    last_row_id: number;
    rows_read: number;
    rows_written: number;
    size_after: number;
  };
}

export interface D1ExecResult {
  count: number;
  duration: number;
}

// 議事録データ型
export interface SpeechRecord {
  id: string;
  date: string;
  session: number;
  house: string;
  committee: string;
  speaker: string;
  party: string;
  party_normalized: string;
  text: string;
  url: string;
  created_at: string;
}

// マニフェストデータ型
export interface ManifestoRecord {
  id: string;
  party_name: string;
  basic_theme?: string;
  target_voters?: string; // JSON文字列
  key_policies?: string;  // JSON文字列
  categories: string;     // JSON文字列
  party_references?: string; // JSON文字列
  updated_at: string;
}

// 質問主意書データ型
export interface QuestionRecord {
  id: string;
  title: string;
  questioner: string;
  submission_date: string;
  status: string;
  answer_date?: string;
  question_url: string;
  answer_url?: string;
  created_at: string;
}

// 法案データ型
export interface BillRecord {
  id: string;
  title: string;
  bill_number: string;
  session: number;
  house: string;
  status: string;
  submission_date: string;
  bill_url: string;
  progress_url?: string;
  created_at: string;
}

// 委員会ニュースデータ型
export interface CommitteeNewsRecord {
  id: string;
  committee: string;
  title: string;
  date: string;
  content: string;
  news_url: string;
  created_at: string;
}