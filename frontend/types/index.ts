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
  meeting_info?: {
    session_name: string;
    meeting_name: string;
    house: string;
    meeting_number: string;
    date: string;
    issue: string;
    pdf_url: string;
    speech_order: string;
    meeting_type: string;
  };
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
  include_meeting_info?: boolean;
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