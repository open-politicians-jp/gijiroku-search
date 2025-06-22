import { MeetingSummary, SummarySearchParams, SummariesResult } from '@/types';

/**
 * 議会要約クライアントサイドローダー（静的エクスポート対応）
 */
export class SummariesClientLoader {
  private static cache: Map<string, { data: MeetingSummary[], timestamp: number }> = new Map();
  private static readonly CACHE_TTL = 5 * 60 * 1000; // 5分間キャッシュ

  /**
   * キャッシュをクリア（開発用）
   */
  static clearCache() {
    this.cache.clear();
  }

  /**
   * キャッシュの有効性をチェック
   */
  private static isCacheValid(timestamp: number): boolean {
    return Date.now() - timestamp < this.CACHE_TTL;
  }

  /**
   * GitHub Pages basePath対応
   */
  private static getBasePath(): string {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      if (path.startsWith('/gijiroku-search/')) {
        return '/gijiroku-search';
      }
    }
    return process.env.GITHUB_PAGES === 'true' ? '/gijiroku-search' : '';
  }

  /**
   * 単一の要約ファイルを読み込み
   */
  private static async loadSummaryFile(fileName: string): Promise<MeetingSummary | null> {
    try {
      const basePath = this.getBasePath();
      // ファイル名をURL エンコード（日本語文字対応）
      const encodedFileName = encodeURIComponent(fileName);
      const url = `${basePath}/data/summaries/${encodedFileName}`;
      
      // デバッグログ（本番環境でのURL確認用）
      console.warn(`🔍 Attempting to load summary: ${url}`);
      console.warn(`📝 Original filename: ${fileName}`);
      console.warn(`🔗 Encoded filename: ${encodedFileName}`);
      
      const response = await fetch(url);
      
      console.warn(`📡 Response status for ${fileName}: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        console.warn(`❌ Failed to load summary file: ${fileName} (${response.status})`);
        
        // フォールバック：エンコードしないURLも試す
        const fallbackUrl = `${basePath}/data/summaries/${fileName}`;
        console.warn(`🔄 Trying fallback URL: ${fallbackUrl}`);
        
        const fallbackResponse = await fetch(fallbackUrl);
        console.warn(`📡 Fallback response status: ${fallbackResponse.status} ${fallbackResponse.statusText}`);
        
        if (!fallbackResponse.ok) {
          return null;
        }
        
        const summary: MeetingSummary = await fallbackResponse.json();
        
        // データ品質チェック
        if (!summary.meeting_info?.date || !summary.meeting_info?.house || !summary.meeting_info?.committee) {
          console.warn(`⚠️ Invalid summary data in ${fileName}`);
          return null;
        }
        
        console.warn(`✅ Successfully loaded via fallback: ${fileName}`);
        return summary;
      }
      
      const summary: MeetingSummary = await response.json();
      
      // データ品質チェック
      if (!summary.meeting_info?.date || !summary.meeting_info?.house || !summary.meeting_info?.committee) {
        console.warn(`⚠️ Invalid summary data in ${fileName}`);
        return null;
      }
      
      console.warn(`✅ Successfully loaded: ${fileName}`);
      return summary;
    } catch (error) {
      console.error(`❌ Error loading summary file ${fileName}:`, error);
      return null;
    }
  }

  /**
   * 利用可能な要約ファイル一覧を取得（静的リスト）
   * 2024年の過去データと2025年の最新データを含む
   */
  private static getSummaryFileNames(): string[] {
    // 静的エクスポート環境では、既知のファイル名をハードコード
    return [
      // 2025年最新データ
      'summary_20250603_衆議_議院運営委員会.json',
      'summary_20250530_衆議_議院運営委員会.json',
      'summary_20250530_参議_議院運営委員会.json',
      'summary_20250528_参議_議院運営委員会.json',
      'summary_20250527_衆議_議院運営委員会.json',
      'summary_20250523_衆議_予算委員会.json',
      'summary_20250523_参議_議院運営委員会.json',
      'summary_20250522_衆議_議院運営委員会.json',
      
      // 2024年過去データ（手動収集済み）
      'summary_20241009_衆議_本会議.json',
      'summary_20241009_衆議_議院運営委員会.json',
      'summary_20241009_参議_本会議.json'
    ];
  }

  /**
   * 全ての要約ファイルを読み込み（クライアントサイド）
   */
  static async loadAllSummaries(): Promise<MeetingSummary[]> {
    try {
      // キャッシュチェック
      const cacheKey = 'all_summaries_client';
      const cached = this.cache.get(cacheKey);
      
      if (cached && this.isCacheValid(cached.timestamp)) {
        console.warn('📦 Using cached summaries data');
        return cached.data;
      }
      
      const fileNames = this.getSummaryFileNames();
      console.warn(`🚀 Loading ${fileNames.length} summary files...`);
      
      // デバッグ用：basePath確認
      const basePath = this.getBasePath();
      console.warn(`🌐 Base path detected: "${basePath}"`);
      console.warn(`🏠 Window location: ${typeof window !== 'undefined' ? window.location.href : 'SSR'}`);

      // 段階的読み込み（並列処理を制限してリソース負荷軽減）
      const BATCH_SIZE = 3; // 一度に3ファイルずつ処理
      const summaries: MeetingSummary[] = [];
      
      for (let i = 0; i < fileNames.length; i += BATCH_SIZE) {
        const batch = fileNames.slice(i, i + BATCH_SIZE);
        console.warn(`📚 Loading batch ${Math.floor(i/BATCH_SIZE) + 1}/${Math.ceil(fileNames.length/BATCH_SIZE)}: ${batch.length} files`);
        
        const batchPromises = batch.map(fileName => this.loadSummaryFile(fileName));
        const batchResults = await Promise.all(batchPromises);
        
        // null値を除外してsummariesに追加
        const validSummaries = batchResults.filter((summary): summary is MeetingSummary => 
          summary !== null
        );
        
        summaries.push(...validSummaries);
        
        // 短い遅延（レート制限対策）
        if (i + BATCH_SIZE < fileNames.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      console.warn(`✅ Successfully loaded ${summaries.length}/${fileNames.length} summary files`);

      // 日付順にソート（新しい順）
      summaries.sort((a, b) => 
        new Date(b.meeting_info.date).getTime() - new Date(a.meeting_info.date).getTime()
      );

      // キャッシュに保存
      this.cache.set(cacheKey, {
        data: summaries,
        timestamp: Date.now()
      });

      return summaries;
    } catch (error) {
      console.error('❌ Error loading summaries:', error);
      // フォールバック：空の配列を返すのではなく、部分的にでも読み込めたデータを返す
      const cachedData = this.cache.get('all_summaries_client');
      if (cachedData) {
        console.warn('🔄 Returning cached data as fallback');
        return cachedData.data;
      }
      return [];
    }
  }

  /**
   * 要約検索（クライアントサイド）
   */
  static async searchSummaries(params: SummarySearchParams): Promise<SummariesResult> {
    const allSummaries = await this.loadAllSummaries();
    let filteredSummaries = allSummaries;

    // テキスト検索
    if (params.q && params.q.trim()) {
      const query = params.q.toLowerCase();
      filteredSummaries = filteredSummaries.filter(summary => 
        summary.summary.text.toLowerCase().includes(query) ||
        summary.meeting_info.committee.toLowerCase().includes(query) ||
        summary.summary.keywords.some(keyword => 
          keyword.toLowerCase().includes(query)
        )
      );
    }

    // 院でフィルター
    if (params.house) {
      filteredSummaries = filteredSummaries.filter(summary =>
        summary.meeting_info.house === params.house
      );
    }

    // 委員会でフィルター
    if (params.committee) {
      filteredSummaries = filteredSummaries.filter(summary =>
        summary.meeting_info.committee.includes(params.committee!)
      );
    }

    // 日付範囲でフィルター
    if (params.date_from) {
      filteredSummaries = filteredSummaries.filter(summary =>
        summary.meeting_info.date >= params.date_from!
      );
    }

    if (params.date_to) {
      filteredSummaries = filteredSummaries.filter(summary =>
        summary.meeting_info.date <= params.date_to!
      );
    }

    // キーワードでフィルター
    if (params.keywords && params.keywords.length > 0) {
      filteredSummaries = filteredSummaries.filter(summary =>
        params.keywords!.some(keyword =>
          summary.summary.keywords.includes(keyword)
        )
      );
    }

    // ページネーション
    const limit = params.limit || 10;
    const offset = params.offset || 0;
    const total = filteredSummaries.length;
    const paginatedSummaries = filteredSummaries.slice(offset, offset + limit);

    return {
      summaries: paginatedSummaries,
      total,
      limit,
      offset,
      has_more: offset + limit < total
    };
  }

  /**
   * 利用可能な院の一覧を取得
   */
  static async getAvailableHouses(): Promise<string[]> {
    const summaries = await this.loadAllSummaries();
    const houses = new Set(summaries.map(s => s.meeting_info.house));
    return Array.from(houses).sort();
  }

  /**
   * 利用可能な委員会の一覧を取得
   */
  static async getAvailableCommittees(): Promise<string[]> {
    const summaries = await this.loadAllSummaries();
    const committees = new Set(summaries.map(s => s.meeting_info.committee));
    return Array.from(committees).sort();
  }

  /**
   * 利用可能なキーワードの一覧を取得
   */
  static async getAvailableKeywords(): Promise<string[]> {
    const summaries = await this.loadAllSummaries();
    const keywords = new Set<string>();
    
    summaries.forEach(summary => {
      summary.summary.keywords.forEach(keyword => keywords.add(keyword));
    });

    return Array.from(keywords).sort();
  }

  /**
   * 統計情報を取得
   */
  static async getSummaryStats() {
    const summaries = await this.loadAllSummaries();
    
    if (summaries.length === 0) {
      return {
        total_summaries: 0,
        total_meetings: 0,
        houses: [],
        committees: [],
        keywords: [],
        date_range: { from: '', to: '' }
      };
    }

    const houses = await this.getAvailableHouses();
    const committees = await this.getAvailableCommittees();
    const keywords = await this.getAvailableKeywords();

    const dates = summaries.map(s => s.meeting_info.date).sort();

    return {
      total_summaries: summaries.length,
      total_meetings: summaries.length,
      houses,
      committees,
      keywords: keywords.slice(0, 20), // 上位20キーワード
      date_range: {
        from: dates[0],
        to: dates[dates.length - 1]
      }
    };
  }
}