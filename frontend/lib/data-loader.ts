/**
 * 静的データローダー（SPA対応）
 * GitHub Pages用の静的データ読み込み機能
 */

import { Speech, SearchResult, Stats, CommitteeNews, Bill, Question, Manifesto, SearchParams } from '@/types';

class StaticDataLoader {
  private speechesCache: Speech[] = [];
  private committeeNewsCache: CommitteeNews[] = [];
  private billsCache: Bill[] = [];
  private questionsCache: Question[] = [];
  private manifestosCache: Manifesto[] = [];
  private statsCache: Stats | null = null;
  
  private lastCacheTime: number = 0;
  private readonly CACHE_DURATION = 30 * 60 * 1000; // 30分キャッシュ
  
  // GitHub Pages basePath対応
  private getBasePath(): string {
    if (typeof window !== 'undefined') {
      // ブラウザ環境では現在のパスから推測
      const path = window.location.pathname;
      if (path.startsWith('/gijiroku-search/')) {
        return '/gijiroku-search';
      }
    }
    const basePath = process.env.GITHUB_PAGES === 'true' ? '/gijiroku-search' : '';
    return basePath;
  }
  
  private getDataPath(path: string): string {
    const basePath = this.getBasePath();
    const fullPath = `${basePath}${path}`;
    return fullPath;
  }

  /**
   * 分割されたスピーチデータを読み込み
   */
  private async loadSpeechesFromChunks(): Promise<Speech[]> {
    try {
      // インデックスファイルを読み込み
      const indexPath = this.getDataPath('/data/speeches/speeches_index.json');
      const indexResponse = await fetch(indexPath);
      
      if (!indexResponse.ok) {
        console.warn('Speeches index not found, falling back to latest');
        return await this.loadSpeechesFromLatest();
      }
      
      const indexData = await indexResponse.json();
      const totalChunks = indexData.metadata.total_chunks;
      
      // GitHub Pages最適化環境での制限対応
      const isOptimizedEnv = indexData.metadata.optimization_applied;
      if (isOptimizedEnv) {
        console.warn('📊 GitHub Pages optimized environment detected - using reduced dataset');
      }
      
      // 全チャンクを並列読み込み
      const chunkPromises = [];
      for (let i = 1; i <= totalChunks; i++) {
        const chunkPath = this.getDataPath(`/data/speeches/speeches_chunk_${i.toString().padStart(2, '0')}.json`);
        chunkPromises.push(
          fetch(chunkPath)
            .then(response => response.ok ? response.json() : null)
            .catch(() => null)
        );
      }
      
      const chunkResults = await Promise.all(chunkPromises);
      const allSpeeches: Speech[] = [];
      
      for (const chunkData of chunkResults) {
        if (chunkData && chunkData.data) {
          allSpeeches.push(...chunkData.data);
        }
      }
      
      // Speeches loaded from chunks
      return allSpeeches;
      
    } catch (error) {
      console.error('Error loading chunked speeches data:', error);
      return await this.loadSpeechesFromLatest();
    }
  }

  /**
   * 従来のlatest.jsonからスピーチデータを読み込み（フォールバック）
   */
  private async loadSpeechesFromLatest(): Promise<Speech[]> {
    try {
      const speechesPath = this.getDataPath('/data/speeches/speeches_latest.json');
      const response = await fetch(speechesPath);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      // Speeches loaded from latest.json
      return data.data || [];
      
    } catch (error) {
      console.error('Error loading speeches from latest.json:', error);
      return [];
    }
  }

  /**
   * 利用可能な議事録ファイル一覧を動的に取得
   * YYYYMMDD_HHMMSS命名規則に対応
   */
  private async getAvailableSpeechFiles(): Promise<string[]> {
    try {
      // speeches_index.json から利用可能ファイル一覧を取得
      const indexPath = this.getDataPath('/data/speeches/speeches_index.json');
      const response = await fetch(indexPath);
      
      if (response.ok) {
        const indexData = await response.json();
        if (indexData.available_files) {
          return indexData.available_files.map((filename: string) => 
            this.getDataPath(`/data/speeches/${filename}`)
          );
        }
      }
    } catch (error) {
      console.warn('speeches_index.json読み込み失敗、フォールバックを使用');
    }

    // フォールバック: 現在の統一命名規則ファイル
    const fallbackFiles = [
      'speeches_20250101_000000.json',
      'speeches_20250203_000000.json',
      'speeches_20250210_000000.json',
      'speeches_20250217_000000.json',
      'speeches_20250224_000000.json',
      'speeches_20250303_000000.json',
      'speeches_20250310_000000.json',
      'speeches_20250317_000000.json',
      'speeches_20250324_000000.json',
      'speeches_20250331_000000.json',
      'speeches_20250407_000000.json',
      'speeches_20250414_000000.json',
      'speeches_20250421_000000.json',
      'speeches_20250428_000000.json',
      'speeches_20250501_000000.json',
      'speeches_20250601_000000.json',
      'speeches_latest.json'
    ];

    return fallbackFiles.map(filename => 
      this.getDataPath(`/data/speeches/${filename}`)
    );
  }

  /**
   * 議事録データを読み込み（分割チャンク対応）
   */
  async loadSpeeches(): Promise<Speech[]> {
    if (this.speechesCache.length > 0 && this.isCacheValid()) {
      return this.speechesCache;
    }

    try {
      // Loading speeches data
      
      // 分割データから読み込み（優先）
      const allSpeeches = await this.loadSpeechesFromChunks();
      
      if (allSpeeches.length === 0) {
        console.warn('loadSpeeches: No speech data could be loaded');
        this.speechesCache = [];
        this.updateCacheTime();
        return this.speechesCache;
      }

      // 重複除去（IDベース）
      const uniqueSpeeches = new Map<string, Speech>();
      allSpeeches.forEach(speech => {
        const key = speech.id || `${speech.date}-${speech.speaker}-${speech.text.substring(0, 50)}`;
        if (!uniqueSpeeches.has(key)) {
          uniqueSpeeches.set(key, speech);
        }
      });

      const finalSpeeches = Array.from(uniqueSpeeches.values());
      
      // 日付順でソート（新しい順）
      finalSpeeches.sort((a, b) => b.date.localeCompare(a.date));
      
      
      this.speechesCache = finalSpeeches;
      this.updateCacheTime();
      return this.speechesCache;
      
    } catch (error) {
      console.error('loadSpeeches: Critical error loading speeches:', error);
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
      // 委員会ニュースデータ読み込み
      const filesToTry = [
        '/data/committee_news/committee_news_latest.json'
      ].map(path => this.getDataPath(path));

      const allNews: CommitteeNews[] = [];
      const seenTitles = new Set<string>(); // 重複除去用

      for (const filePath of filesToTry) {
        try {
          const response = await fetch(filePath);
          if (response.ok) {
            const data = await response.json();
            const newsItems = Array.isArray(data) ? data : data.data || [];
            
            // 重複除去しながら統合
            for (const item of newsItems) {
              if (item.title && !seenTitles.has(item.title)) {
                seenTitles.add(item.title);
                allNews.push(item);
              }
            }
          }
        } catch (fileError) {
          console.warn(`委員会ニュースファイル読み込みエラー: ${filePath}`, fileError);
          continue;
        }
      }
      
      // 日付順でソート（新しい順）
      allNews.sort((a, b) => {
        const dateA = a.date || a.collected_at;
        const dateB = b.date || b.collected_at;
        return dateB.localeCompare(dateA);
      });
      
      this.committeeNewsCache = allNews;
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
      ].map(path => this.getDataPath(path));

      for (const filePath of filesToTry) {
        try {
          const response = await fetch(filePath);
          if (response.ok) {
            const data = await response.json();
            
            // データ構造の変換処理
            const rawBills = Array.isArray(data) ? data : data.bills || data.data || [];
            
            this.billsCache = rawBills.map((bill: any) => ({
              bill_number: bill.bill_number || '',
              title: bill.title || bill.status || '', // statusが実際のタイトルの場合がある
              submitter: bill.submitter || '',
              status: bill.submission_date || bill.status || '', // submission_dateが実際のステータスの場合がある
              status_normalized: bill.status_normalized || bill.submission_date || bill.status || '',
              session_number: bill.session_number || bill.session || parseInt(bill.bill_number) || 0,
              detail_url: bill.bill_url || bill.url || bill.content_url || bill.detail_url || '',
              summary: bill.summary || bill.bill_summary || bill.bill_content || '',
              committee: bill.committee || '',
              submission_date: bill.submission_date || bill.created_at || bill.collected_at || '',
              related_urls: (bill.related_links || bill.related_urls || []).map((link: any) => ({
                title: link.title || '関連資料',
                url: link.url || ''
              })),
              collected_at: bill.collected_at || bill.created_at || new Date().toISOString(),
              year: bill.year || new Date().getFullYear(),
              full_text: bill.full_text || bill.content || bill.bill_summary || ''
            }));
            
            this.updateCacheTime();
            return this.billsCache;
          }
        } catch (fileError) {
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
      ].map(path => this.getDataPath(path));

      for (const filePath of filesToTry) {
        try {
          const response = await fetch(filePath);
          if (response.ok) {
            const data = await response.json();
            
            // データ構造の変換処理
            const rawQuestions = Array.isArray(data) ? data : data.questions || data.data || [];
            
            this.questionsCache = rawQuestions.map((question: any) => ({
              title: question.title || '',
              question_number: question.question_number || '',
              questioner: question.questioner || '',
              house: question.house || '衆議院',
              submission_date: question.submission_date || '',
              answer_date: question.answer_date || '',
              question_content: question.question_content || '',
              answer_content: question.answer_content || '',
              question_url: question.question_url || '',
              answer_url: question.answer_url || '',
              category: question.category || '',
              html_links: question.html_links || [],
              pdf_links: question.pdf_links || [],
              collected_at: question.collected_at || new Date().toISOString(),
              year: question.year || new Date().getFullYear(),
              week: question.week || 1
            }));
            
            this.updateCacheTime();
            return this.questionsCache;
          }
        } catch (fileError) {
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
      
      if (speeches.length === 0) {
        console.warn('loadStats: No speeches loaded, returning default stats');
        const defaultStats = this.getDefaultStats();
        return defaultStats;
      }
      
      
      // 統計を動的計算
      const stats: Stats = this.calculateStats(speeches);
      
      
      this.statsCache = stats;
      this.updateCacheTime();
      return stats;
    } catch (error) {
      console.error('loadStats: Error loading stats:', error);
      const defaultStats = this.getDefaultStats();
      return defaultStats;
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
   * マニフェスト読み込み
   */
  async loadManifestos(): Promise<Manifesto[]> {
    if (this.manifestosCache.length > 0 && this.isCacheValid()) {
      return this.manifestosCache;
    }

    try {
      const response = await fetch(this.getDataPath('/data/manifestos/manifestos_latest.json'));
      if (!response.ok) {
        throw new Error('マニフェストデータの読み込みに失敗しました');
      }

      const data = await response.json();
      this.manifestosCache = data.data || [];
      this.updateCacheTime();
      
      return this.manifestosCache;
    } catch (error) {
      console.error('マニフェスト読み込みエラー:', error);
      return [];
    }
  }

  /**
   * マニフェスト検索
   */
  async searchManifestos(params: SearchParams) {
    const manifestos = await this.loadManifestos();
    return this.performManifestosSearch(manifestos, params);
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
      case 'manifestos':
        return this.searchManifestos(params);
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

    // 提出者検索
    if (params.bill_submitter) {
      const submitter = params.bill_submitter.toLowerCase();
      filteredBills = filteredBills.filter(bill =>
        bill.submitter.toLowerCase().includes(submitter)
      );
    }

    // ステータス検索
    if (params.bill_status) {
      const status = params.bill_status.toLowerCase();
      filteredBills = filteredBills.filter(bill =>
        bill.status.toLowerCase().includes(status) ||
        bill.status_normalized.toLowerCase().includes(status)
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

    // URLを正規化・フィルタリング
    const processedBills = paginatedBills.map(bill => ({
      ...bill,
      detail_url: bill.detail_url ? this.normalizeUrl(bill.detail_url) : '',
      related_urls: bill.related_urls ? bill.related_urls
        .map(link => ({
          ...link,
          url: this.normalizeBillUrl(link.url, bill.session_number, bill.bill_number)
        }))
        .filter(link => {
          // 審議経過URLの有効性チェック
          if (link.title?.includes('審議経過') && link.url.includes('keika/')) {
            // URLパターンが正しいかチェック（第217回国会の場合）
            const urlPattern = /keika\/217\d{4}\.htm$/;
            if (!urlPattern.test(link.url)) {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`法案検索: 無効な審議経過URLパターン - ${link.url}`);
              }
              return false;
            }
            // 有効なパターンでも404の可能性があるURLは除外
            const billNumber = link.url.match(/217(\d{4})/)?.[1];
            if (billNumber && parseInt(billNumber) > 200) {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`法案検索: 存在しない可能性のある法案番号 - ${billNumber}`);
              }
              return false;
            }
          }
          return true;
        }) : []
    }));

    return {
      bills: processedBills,
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
    if (params.speaker || params.questioner) {
      const questioner = (params.speaker || params.questioner || '').toLowerCase();
      filteredQuestions = filteredQuestions.filter(question =>
        question.questioner && question.questioner.toLowerCase().includes(questioner)
      );
    }

    // 会期番号検索
    if (params.session_number) {
      const sessionNumber = params.session_number;
      filteredQuestions = filteredQuestions.filter(question =>
        question.question_number && question.question_number.includes(sessionNumber)
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

  private performManifestosSearch(manifestos: Manifesto[], params: SearchParams) {
    let filteredManifestos = [...manifestos];

    // テキスト検索
    if (params.q) {
      const query = params.q.toLowerCase();
      filteredManifestos = filteredManifestos.filter(manifesto =>
        manifesto.title.toLowerCase().includes(query) ||
        manifesto.content.toLowerCase().includes(query) ||
        manifesto.party.toLowerCase().includes(query) ||
        (manifesto.category && manifesto.category.toLowerCase().includes(query))
      );
    }

    // 政党検索
    if (params.party) {
      const party = params.party.toLowerCase();
      filteredManifestos = filteredManifestos.filter(manifesto =>
        manifesto.party.toLowerCase().includes(party) ||
        (manifesto.party_aliases && manifesto.party_aliases.some(alias => 
          alias.toLowerCase().includes(party)
        ))
      );
    }

    // カテゴリ検索（委員会パラメータを流用）
    if (params.committee) {
      const category = params.committee.toLowerCase();
      filteredManifestos = filteredManifestos.filter(manifesto =>
        manifesto.category && manifesto.category.toLowerCase().includes(category)
      );
    }

    // 年検索（日付範囲を年として使用）
    if (params.date_from) {
      const yearFrom = parseInt(params.date_from);
      if (!isNaN(yearFrom)) {
        filteredManifestos = filteredManifestos.filter(manifesto =>
          manifesto.year >= yearFrom
        );
      }
    }

    if (params.date_to) {
      const yearTo = parseInt(params.date_to);
      if (!isNaN(yearTo)) {
        filteredManifestos = filteredManifestos.filter(manifesto =>
          manifesto.year <= yearTo
        );
      }
    }

    // 収集日時順でソート（新しい順）
    filteredManifestos.sort((a, b) => b.collected_at.localeCompare(a.collected_at));

    const total = filteredManifestos.length;
    const limit = params.limit || 20;
    const offset = params.offset || 0;

    const paginatedManifestos = filteredManifestos.slice(offset, offset + limit);

    return {
      manifestos: paginatedManifestos,
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

  private normalizeBillUrl(url: string, sessionNumber: number, billNumber: string): string {
    if (!url) return '';
    
    // 通常のURL正規化を適用
    return this.normalizeUrl(url);
  }

  private calculateStats(speeches: Speech[]): Stats {
    
    // 政党別集計
    const partyCount: { [key: string]: number } = {};
    const speakerCount: { [key: string]: number } = {};
    const committeeCount: { [key: string]: number } = {};
    
    let minDate = '';
    let maxDate = '';

    speeches.forEach((speech, index) => {
      // データ品質チェック（最初の10件）
      
      // 政党集計（null値のチェック）
      if (speech.party && speech.party.trim() !== '') {
        const party = speech.party.trim();
        partyCount[party] = (partyCount[party] || 0) + 1;
      }
      
      // 発言者集計
      if (speech.speaker && speech.speaker.trim() !== '') {
        const speaker = speech.speaker.trim();
        speakerCount[speaker] = (speakerCount[speaker] || 0) + 1;
      }
      
      // 委員会集計
      if (speech.committee && speech.committee.trim() !== '') {
        const committee = speech.committee.trim();
        committeeCount[committee] = (committeeCount[committee] || 0) + 1;
      }
      
      // 日付範囲
      if (speech.date && speech.date.trim() !== '') {
        const date = speech.date.trim();
        if (!minDate || date < minDate) minDate = date;
        if (!maxDate || date > maxDate) maxDate = date;
      }
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