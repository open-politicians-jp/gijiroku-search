/**
 * 静的データローダー（SPA対応）
 * GitHub Pages用の静的データ読み込み機能
 */

import { Speech, SearchResult, Stats, CommitteeNews, Bill, Question } from '@/types';

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

class StaticDataLoader {
  private speechesCache: Speech[] = [];
  private committeeNewsCache: CommitteeNews[] = [];
  private billsCache: Bill[] = [];
  private questionsCache: Question[] = [];
  private statsCache: Stats | null = null;
  
  private lastCacheTime: number = 0;
  private readonly CACHE_DURATION = 30 * 60 * 1000; // 30分キャッシュ

  /**
   * 議事録データを読み込み
   */
  async loadSpeeches(): Promise<Speech[]> {
    if (this.speechesCache.length > 0 && this.isCacheValid()) {
      return this.speechesCache;
    }

    try {
      // 利用可能なファイルを優先順位で試行
      const filesToTry = [
        '/data/speeches/speeches_2025_processed.json',
        '/data/speeches/speeches_20250610_112452.json',
        '/data/speeches/speeches_20250610_110612.json',
        '/data/speeches/speeches_20250610_105520.json',
        '/data/speeches/speeches_20250610_000325.json',
        '/data/speeches/speeches_20250609_232138.json'
      ];

      for (const filePath of filesToTry) {
        try {
          const response = await fetch(filePath);
          if (response.ok) {
            const data = await response.json();
            console.log(`Loaded speeches from: ${filePath}`);
            
            if (Array.isArray(data)) {
              this.speechesCache = data;
            } else if (data.speeches && Array.isArray(data.speeches)) {
              this.speechesCache = data.speeches;
            } else if (data.data && Array.isArray(data.data)) {
              this.speechesCache = data.data;
            } else {
              console.warn(`Unexpected data format in ${filePath}:`, data);
              continue;
            }
            
            this.updateCacheTime();
            console.log(`Loaded ${this.speechesCache.length} speeches`);
            return this.speechesCache;
          }
        } catch (fileError) {
          console.log(`Failed to load ${filePath}:`, fileError);
          continue;
        }
      }
      
      console.warn('No speech files could be loaded');
      this.speechesCache = [];
      this.updateCacheTime();
      return this.speechesCache;
    } catch (error) {
      console.error('Error loading speeches:', error);
      return [];
    }
  }

  /**
   * 委員会ニュースデータを読み込み
   */
  async loadCommitteeNews(): Promise<CommitteeNews[]> {
    if (this.committeeNewsCache.length > 0 && this.isCacheValid()) {
      return this.committeeNewsCache;
    }

    try {
      const filesToTry = [
        '/data/committee_news/committee_news_latest.json',
        '/data/committee_news/committee_news_20250612_012023.json'
      ];

      for (const filePath of filesToTry) {
        try {
          const response = await fetch(filePath);
          if (response.ok) {
            const data = await response.json();
            console.log(`Loaded committee news from: ${filePath}`);
            
            this.committeeNewsCache = Array.isArray(data) ? data : data.data || [];
            this.updateCacheTime();
            console.log(`Loaded ${this.committeeNewsCache.length} committee news items`);
            return this.committeeNewsCache;
          }
        } catch (fileError) {
          console.log(`Failed to load ${filePath}:`, fileError);
          continue;
        }
      }
      
      console.warn('No committee news files could be loaded');
      this.committeeNewsCache = [];
      this.updateCacheTime();
      return this.committeeNewsCache;
    } catch (error) {
      console.error('Error loading committee news:', error);
      return [];
    }
  }

  /**
   * 法案データを読み込み
   */
  async loadBills(): Promise<Bill[]> {
    if (this.billsCache.length > 0 && this.isCacheValid()) {
      return this.billsCache;
    }

    try {
      const filesToTry = [
        '/data/bills/bills_latest.json',
        '/data/bills/bills_realistic_20250617_085841.json',
        '/data/bills/bills_20250617_084742.json',
        '/data/bills/bills_20250611_200440.json'
      ];

      for (const filePath of filesToTry) {
        try {
          const response = await fetch(filePath);
          if (response.ok) {
            const data = await response.json();
            console.log(`Loaded bills from: ${filePath}`);
            
            this.billsCache = Array.isArray(data) ? data : data.bills || data.data || [];
            this.updateCacheTime();
            console.log(`Loaded ${this.billsCache.length} bills`);
            return this.billsCache;
          }
        } catch (fileError) {
          console.log(`Failed to load ${filePath}:`, fileError);
          continue;
        }
      }
      
      console.warn('No bill files could be loaded');
      this.billsCache = [];
      this.updateCacheTime();
      return this.billsCache;
    } catch (error) {
      console.error('Error loading bills:', error);
      return [];
    }
  }

  /**
   * 質問主意書データを読み込み
   */
  async loadQuestions(): Promise<Question[]> {
    if (this.questionsCache.length > 0 && this.isCacheValid()) {
      return this.questionsCache;
    }

    try {
      const filesToTry = [
        '/data/questions/questions_latest.json',
        '/data/questions/questions_enhanced_20250617_084938.json',
        '/data/questions/questions_20250617_083722.json',
        '/data/questions/questions_20250611_200440.json'
      ];

      for (const filePath of filesToTry) {
        try {
          const response = await fetch(filePath);
          if (response.ok) {
            const data = await response.json();
            console.log(`Loaded questions from: ${filePath}`);
            
            this.questionsCache = Array.isArray(data) ? data : data.questions || data.data || [];
            this.updateCacheTime();
            console.log(`Loaded ${this.questionsCache.length} questions`);
            return this.questionsCache;
          }
        } catch (fileError) {
          console.log(`Failed to load ${filePath}:`, fileError);
          continue;
        }
      }
      
      console.warn('No question files could be loaded');
      this.questionsCache = [];
      this.updateCacheTime();
      return this.questionsCache;
    } catch (error) {
      console.error('Error loading questions:', error);
      return [];
    }
  }

  /**
   * 統計データを読み込み
   */
  async loadStats(): Promise<Stats> {
    if (this.statsCache && this.isCacheValid()) {
      return this.statsCache;
    }

    try {
      const speeches = await this.loadSpeeches();
      
      // 統計を動的計算
      const stats: Stats = this.calculateStats(speeches);
      
      this.statsCache = stats;
      this.updateCacheTime();
      return stats;
    } catch (error) {
      console.error('Error loading stats:', error);
      return this.getDefaultStats();
    }
  }

  /**
   * 議事録検索
   */
  async searchSpeeches(params: SearchParams): Promise<SearchResult> {
    const speeches = await this.loadSpeeches();
    return this.performSpeechSearch(speeches, params);
  }

  /**
   * 委員会ニュース検索
   */
  async searchCommitteeNews(params: SearchParams) {
    const news = await this.loadCommitteeNews();
    return this.performCommitteeNewsSearch(news, params);
  }

  /**
   * 法案検索
   */
  async searchBills(params: SearchParams) {
    const bills = await this.loadBills();
    return this.performBillsSearch(bills, params);
  }

  /**
   * 質問主意書検索
   */
  async searchQuestions(params: SearchParams) {
    const questions = await this.loadQuestions();
    return this.performQuestionsSearch(questions, params);
  }

  /**
   * 統合検索
   */
  async search(params: SearchParams): Promise<SearchResult | any> {
    switch (params.search_type) {
      case 'committee_news':
        return this.searchCommitteeNews(params);
      case 'bills':
        return this.searchBills(params);
      case 'questions':
        return this.searchQuestions(params);
      default:
        return this.searchSpeeches(params);
    }
  }

  // プライベートメソッド

  private isCacheValid(): boolean {
    const now = Date.now();
    return (now - this.lastCacheTime) < this.CACHE_DURATION;
  }

  private updateCacheTime(): void {
    this.lastCacheTime = Date.now();
  }

  private performSpeechSearch(speeches: Speech[], params: SearchParams): SearchResult {
    let filteredSpeeches = [...speeches];

    // テキスト検索
    if (params.q) {
      const query = params.q.toLowerCase();
      filteredSpeeches = filteredSpeeches.filter(speech =>
        speech.text.toLowerCase().includes(query) ||
        speech.speaker.toLowerCase().includes(query) ||
        (speech.party && speech.party.toLowerCase().includes(query))
      );
    }

    // 発言者検索
    if (params.speaker) {
      const speaker = params.speaker.toLowerCase();
      filteredSpeeches = filteredSpeeches.filter(speech =>
        speech.speaker.toLowerCase().includes(speaker)
      );
    }

    // 政党検索
    if (params.party) {
      const party = params.party.toLowerCase();
      filteredSpeeches = filteredSpeeches.filter(speech =>
        speech.party && speech.party.toLowerCase().includes(party)
      );
    }

    // 委員会検索
    if (params.committee) {
      const committee = params.committee.toLowerCase();
      filteredSpeeches = filteredSpeeches.filter(speech =>
        speech.committee.toLowerCase().includes(committee)
      );
    }

    // 日付範囲検索
    if (params.date_from && params.date_to) {
      filteredSpeeches = filteredSpeeches.filter(speech => {
        return speech.date >= params.date_from! && speech.date <= params.date_to!;
      });
    }

    // 日付順でソート（新しい順）
    filteredSpeeches.sort((a, b) => b.date.localeCompare(a.date));

    const total = filteredSpeeches.length;
    const limit = params.limit || 50;
    const offset = params.offset || 0;

    const paginatedSpeeches = filteredSpeeches.slice(offset, offset + limit);

    return {
      speeches: paginatedSpeeches,
      total,
      limit,
      offset,
      has_more: offset + limit < total
    };
  }

  private performCommitteeNewsSearch(news: CommitteeNews[], params: SearchParams) {
    let filteredNews = [...news];

    // テキスト検索
    if (params.q) {
      const query = params.q.toLowerCase();
      filteredNews = filteredNews.filter(item =>
        item.title.toLowerCase().includes(query) ||
        (item.content && item.content.toLowerCase().includes(query))
      );
    }

    // 委員会検索
    if (params.committee) {
      const committee = params.committee.toLowerCase();
      filteredNews = filteredNews.filter(item =>
        item.committee.toLowerCase().includes(committee)
      );
    }

    // 日付範囲検索
    if (params.date_from && params.date_to) {
      filteredNews = filteredNews.filter(item => {
        if (!item.date) return false;
        return item.date >= params.date_from! && item.date <= params.date_to!;
      });
    }

    // 収集日時順でソート（新しい順）
    filteredNews.sort((a, b) => b.collected_at.localeCompare(a.collected_at));

    const total = filteredNews.length;
    const limit = params.limit || 20;
    const offset = params.offset || 0;

    const paginatedNews = filteredNews.slice(offset, offset + limit);

    return {
      news: paginatedNews,
      total,
      limit,
      offset,
      has_more: offset + limit < total
    };
  }

  private performBillsSearch(bills: Bill[], params: SearchParams) {
    let filteredBills = [...bills];

    // テキスト検索
    if (params.q) {
      const query = params.q.toLowerCase();
      filteredBills = filteredBills.filter(bill =>
        bill.title.toLowerCase().includes(query) ||
        (bill.summary && bill.summary.toLowerCase().includes(query))
      );
    }

    // 委員会検索
    if (params.committee) {
      const committee = params.committee.toLowerCase();
      filteredBills = filteredBills.filter(bill =>
        bill.committee.toLowerCase().includes(committee)
      );
    }

    // 日付範囲検索
    if (params.date_from && params.date_to) {
      filteredBills = filteredBills.filter(bill => {
        if (!bill.submission_date) return false;
        return bill.submission_date >= params.date_from! && bill.submission_date <= params.date_to!;
      });
    }

    // 収集日時順でソート（新しい順）
    filteredBills.sort((a, b) => b.collected_at.localeCompare(a.collected_at));

    const total = filteredBills.length;
    const limit = params.limit || 20;
    const offset = params.offset || 0;

    const paginatedBills = filteredBills.slice(offset, offset + limit);

    return {
      bills: paginatedBills,
      total,
      limit,
      offset,
      has_more: offset + limit < total
    };
  }

  private performQuestionsSearch(questions: Question[], params: SearchParams) {
    let filteredQuestions = [...questions];

    // テキスト検索
    if (params.q) {
      const query = params.q.toLowerCase();
      filteredQuestions = filteredQuestions.filter(question =>
        (question.title && question.title.toLowerCase().includes(query)) ||
        (question.question_content && question.question_content.toLowerCase().includes(query)) ||
        (question.answer_content && question.answer_content.toLowerCase().includes(query)) ||
        (question.questioner && question.questioner.toLowerCase().includes(query)) ||
        (question.category && question.category.toLowerCase().includes(query))
      );
    }

    // 質問者検索
    if (params.speaker) {
      const questioner = params.speaker.toLowerCase();
      filteredQuestions = filteredQuestions.filter(question =>
        question.questioner && question.questioner.toLowerCase().includes(questioner)
      );
    }

    // 日付範囲検索
    if (params.date_from && params.date_to) {
      filteredQuestions = filteredQuestions.filter(question => {
        if (!question.submission_date) return false;
        return question.submission_date >= params.date_from! && question.submission_date <= params.date_to!;
      });
    }

    // カテゴリ検索
    if (params.committee) {
      const category = params.committee.toLowerCase();
      filteredQuestions = filteredQuestions.filter(question =>
        question.category && question.category.toLowerCase().includes(category)
      );
    }

    // 提出日順でソート（新しい順）、フォールバックは収集日時
    filteredQuestions.sort((a, b) => {
      const dateA = a.submission_date || a.collected_at;
      const dateB = b.submission_date || b.collected_at;
      return dateB.localeCompare(dateA);
    });

    const total = filteredQuestions.length;
    const limit = params.limit || 20;
    const offset = params.offset || 0;

    const paginatedQuestions = filteredQuestions.slice(offset, offset + limit);

    // HTMLリンクとPDFリンクのURLを正規化
    const processedQuestions = paginatedQuestions.map(question => ({
      ...question,
      html_links: question.html_links ? question.html_links.map(link => ({
        ...link,
        url: this.normalizeUrl(link.url)
      })) : [],
      pdf_links: question.pdf_links ? question.pdf_links.map(link => ({
        ...link,
        url: this.normalizeUrl(link.url)
      })) : [],
      question_url: question.question_url ? this.normalizeUrl(question.question_url) : '',
      answer_url: question.answer_url ? this.normalizeUrl(question.answer_url) : ''
    }));

    return {
      questions: processedQuestions,
      total,
      limit,
      offset,
      has_more: offset + limit < total
    };
  }

  private normalizeUrl(url: string): string {
    if (!url) return '';
    
    // 既に完全なURLの場合はそのまま返す
    if (url.startsWith('http')) {
      return url;
    }
    
    // 相対パス「../../../」を処理
    if (url.startsWith('../')) {
      const cleanPath = url.replace(/^\.\.\/+/, '');
      return `https://www.shugiin.go.jp/internet/${cleanPath}`;
    }
    
    // その他の相対パス
    if (url.startsWith('/')) {
      return `https://www.shugiin.go.jp${url}`;
    }
    
    // 相対パス（現在ディレクトリ）
    return `https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/${url}`;
  }

  private calculateStats(speeches: Speech[]): Stats {
    // 政党別集計
    const partyCount: { [key: string]: number } = {};
    const speakerCount: { [key: string]: number } = {};
    const committeeCount: { [key: string]: number } = {};
    
    let minDate = '';
    let maxDate = '';

    speeches.forEach(speech => {
      // 政党集計
      if (speech.party) {
        partyCount[speech.party] = (partyCount[speech.party] || 0) + 1;
      }
      
      // 発言者集計
      speakerCount[speech.speaker] = (speakerCount[speech.speaker] || 0) + 1;
      
      // 委員会集計
      committeeCount[speech.committee] = (committeeCount[speech.committee] || 0) + 1;
      
      // 日付範囲
      if (!minDate || speech.date < minDate) minDate = speech.date;
      if (!maxDate || speech.date > maxDate) maxDate = speech.date;
    });

    // 上位項目をソート
    const topParties = Object.entries(partyCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10);
      
    const topSpeakers = Object.entries(speakerCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 20);
      
    const topCommittees = Object.entries(committeeCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 15);

    return {
      total_speeches: speeches.length,
      top_parties: topParties,
      top_speakers: topSpeakers,
      top_committees: topCommittees,
      date_range: {
        from: minDate,
        to: maxDate
      },
      last_updated: new Date().toISOString()
    };
  }

  private getDefaultStats(): Stats {
    return {
      total_speeches: 0,
      top_parties: [],
      top_speakers: [],
      top_committees: [],
      date_range: {
        from: '',
        to: ''
      },
      last_updated: new Date().toISOString()
    };
  }
}

// シングルトンインスタンス
export const dataLoader = new StaticDataLoader();