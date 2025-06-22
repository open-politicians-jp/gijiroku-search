export interface Speech {
  id: string;
  date: string;
  session: number;
  house: string;
  committee: string;
  speaker: string;
  party: string | null;
  text: string;
  url: string;
  created_at: string;
}

export interface SearchParams {
  q?: string;
  speaker?: string;
  party?: string;
  committee?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
  search_type?: 'speeches' | 'committee_news' | 'bills' | 'questions';
}

export interface SearchResult {
  speeches: Speech[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Stats {
  total_speeches: number;
  top_parties: [string, number][];
  top_speakers: [string, number][];
  top_committees: [string, number][];
  date_range: {
    from: string;
    to: string;
  };
  last_updated: string;
}

export interface KokkaiAPIResponse {
  numberOfRecords: number;
  numberOfReturn: number;
  startRecord: number;
  nextRecordPosition?: number;
  speechRecord: KokkaiSpeech[];
}

export interface KokkaiSpeech {
  speechID: string;
  session: number;
  nameOfHouse: string;
  nameOfMeeting: string;
  date: string;
  speaker: string;
  speakerGroup: string | null;
  speech: string;
  speechURL: string;
}

export interface CommitteeNews {
  title: string;
  url: string;
  committee: string;
  date: string | null;
  news_type: string;
  collected_at: string;
  year: number;
  week: number;
  content?: string;
  content_length?: number;
}

export interface CommitteeNewsResult {
  news: CommitteeNews[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Bill {
  bill_number: string;
  title: string;
  submitter: string;
  status: string;
  status_normalized: string;
  session_number: number;
  detail_url: string;
  summary: string;
  full_text?: string;
  committee: string;
  submission_date: string;
  related_urls: Array<{
    title: string;
    url: string;
  }>;
  collected_at: string;
  year: number;
}

export interface BillsResult {
  bills: Bill[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Question {
  title: string;
  question_number: string;
  questioner: string;
  house: string;
  submission_date: string;
  answer_date: string;
  question_content: string;
  answer_content: string;
  question_url: string;
  answer_url: string;
  category: string;
  html_links?: Array<{
    url: string;
    title: string;
    type?: string;
  }>;
  pdf_links?: Array<{
    url: string;
    title: string;
    type?: string;
  }>;
  collected_at: string;
  year: number;
  week: number;
}

export interface QuestionsResult {
  questions: Question[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// 議会要約関連の型定義
export interface MeetingSummary {
  metadata: {
    summary_type: string;
    meeting_key: string;
    generated_at: string;
    model_used: string;
    speech_count: number;
    speakers_count: number;
    parties_count: number;
  };
  meeting_info: {
    date: string;
    house: string;
    committee: string;
    session: number;
    meeting_key: string;
  };
  summary: {
    text: string;
    length: number;
    keywords: string[];
  };
  participants: {
    speakers: string[];
    parties: string[];
  };
  speeches_references: Array<{
    speech_id: string;
    speaker: string;
    url: string;
  }>;
}

export interface SummarySearchParams {
  q?: string;
  house?: string;
  committee?: string;
  date_from?: string;
  date_to?: string;
  keywords?: string[];
  limit?: number;
  offset?: number;
}

export interface SummariesResult {
  summaries: MeetingSummary[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}