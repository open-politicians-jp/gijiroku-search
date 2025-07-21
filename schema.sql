-- D1データベーススキーマ定義
-- 日本政治議事録検索システム用

-- 議事録テーブル
CREATE TABLE speeches (
  id TEXT PRIMARY KEY,
  date TEXT NOT NULL,
  session INTEGER NOT NULL,
  house TEXT NOT NULL,
  committee TEXT NOT NULL,
  speaker TEXT NOT NULL,
  party TEXT NOT NULL,
  party_normalized TEXT NOT NULL,
  text TEXT NOT NULL,
  url TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- 議事録検索用インデックス
CREATE INDEX idx_speeches_date ON speeches(date);
CREATE INDEX idx_speeches_speaker ON speeches(speaker);
CREATE INDEX idx_speeches_party ON speeches(party_normalized);
CREATE INDEX idx_speeches_committee ON speeches(committee);
CREATE INDEX idx_speeches_session ON speeches(session);
CREATE INDEX idx_speeches_house ON speeches(house);

-- 全文検索用インデックス（発言内容）
CREATE INDEX idx_speeches_text ON speeches(text);

-- マニフェストテーブル
CREATE TABLE manifestos (
  id TEXT PRIMARY KEY,
  party_name TEXT NOT NULL UNIQUE,
  basic_theme TEXT,
  target_voters TEXT, -- JSON文字列
  key_policies TEXT,  -- JSON文字列
  categories TEXT NOT NULL, -- JSON文字列
  party_references TEXT, -- JSON文字列
  updated_at TEXT NOT NULL
);

-- マニフェスト検索用インデックス
CREATE INDEX idx_manifestos_party ON manifestos(party_name);

-- 質問主意書テーブル
CREATE TABLE questions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  questioner TEXT NOT NULL,
  submission_date TEXT NOT NULL,
  status TEXT NOT NULL,
  answer_date TEXT,
  question_url TEXT NOT NULL,
  answer_url TEXT,
  created_at TEXT NOT NULL
);

-- 質問主意書検索用インデックス
CREATE INDEX idx_questions_date ON questions(submission_date);
CREATE INDEX idx_questions_questioner ON questions(questioner);
CREATE INDEX idx_questions_status ON questions(status);
CREATE INDEX idx_questions_title ON questions(title);

-- 法案テーブル
CREATE TABLE bills (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  bill_number TEXT NOT NULL,
  session INTEGER NOT NULL,
  house TEXT NOT NULL,
  status TEXT NOT NULL,
  submission_date TEXT NOT NULL,
  bill_url TEXT NOT NULL,
  progress_url TEXT,
  created_at TEXT NOT NULL
);

-- 法案検索用インデックス
CREATE INDEX idx_bills_session ON bills(session);
CREATE INDEX idx_bills_house ON bills(house);
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_date ON bills(submission_date);
CREATE INDEX idx_bills_number ON bills(bill_number);
CREATE INDEX idx_bills_title ON bills(title);

-- 委員会ニューステーブル
CREATE TABLE committee_news (
  id TEXT PRIMARY KEY,
  committee TEXT NOT NULL,
  title TEXT NOT NULL,
  date TEXT NOT NULL,
  content TEXT NOT NULL,
  news_url TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- 委員会ニュース検索用インデックス
CREATE INDEX idx_committee_news_committee ON committee_news(committee);
CREATE INDEX idx_committee_news_date ON committee_news(date);
CREATE INDEX idx_committee_news_title ON committee_news(title);

-- 統計情報用ビュー
CREATE VIEW speech_stats AS
SELECT 
  COUNT(*) as total_speeches,
  COUNT(DISTINCT speaker) as total_speakers,
  COUNT(DISTINCT party_normalized) as total_parties,
  COUNT(DISTINCT committee) as total_committees,
  COUNT(DISTINCT session) as total_sessions,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM speeches;

-- 政党別統計ビュー
CREATE VIEW party_stats AS
SELECT 
  party_normalized as party,
  COUNT(*) as speech_count,
  COUNT(DISTINCT speaker) as speaker_count,
  COUNT(DISTINCT committee) as committee_count,
  MIN(date) as first_speech_date,
  MAX(date) as latest_speech_date
FROM speeches
GROUP BY party_normalized
ORDER BY speech_count DESC;

-- 発言者別統計ビュー  
CREATE VIEW speaker_stats AS
SELECT 
  speaker,
  party_normalized as party,
  COUNT(*) as speech_count,
  COUNT(DISTINCT committee) as committee_count,
  COUNT(DISTINCT session) as session_count,
  MIN(date) as first_speech_date,
  MAX(date) as latest_speech_date
FROM speeches
GROUP BY speaker, party_normalized
ORDER BY speech_count DESC;

-- 委員会別統計ビュー
CREATE VIEW committee_stats AS
SELECT 
  committee,
  COUNT(*) as speech_count,
  COUNT(DISTINCT speaker) as speaker_count,
  COUNT(DISTINCT party_normalized) as party_count,
  MIN(date) as first_activity_date,
  MAX(date) as latest_activity_date
FROM speeches
GROUP BY committee
ORDER BY speech_count DESC;