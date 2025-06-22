import { MeetingSummary, SummarySearchParams, SummariesResult } from '@/types';
import { promises as fs } from 'fs';
import path from 'path';

/**
 * 議会要約データローダー（本番環境最適化版）
 */
export class SummariesLoader {
  private dataDir: string;
  private static cache: Map<string, { data: MeetingSummary[], timestamp: number }> = new Map();
  private static readonly CACHE_TTL = 5 * 60 * 1000; // 5分間キャッシュ

  constructor() {
    this.dataDir = path.join(process.cwd(), 'public', 'data', 'summaries');
  }

  /**
   * キャッシュをクリア（開発用）
   */
  static clearCache() {
    this.cache.clear();
  }

  /**
   * キャッシュの有効性をチェック
   */
  private isCacheValid(timestamp: number): boolean {
    return Date.now() - timestamp < SummariesLoader.CACHE_TTL;
  }

  /**
   * 全ての要約ファイルを読み込み（動的ファイル検出対応・キャッシュ対応）
   */
  async loadAllSummaries(): Promise<MeetingSummary[]> {
    try {
      // キャッシュチェック
      const cacheKey = 'all_summaries';
      const cached = SummariesLoader.cache.get(cacheKey);
      
      if (cached && this.isCacheValid(cached.timestamp)) {
        console.log(`📋 Using cached summaries (${cached.data.length} items)`);
        return cached.data;
      }

      // ディレクトリが存在しない場合は作成
      try {
        await fs.access(this.dataDir);
      } catch {
        console.warn(`Summaries directory not found: ${this.dataDir}`);
        return [];
      }

      const files = await fs.readdir(this.dataDir);
      const summaryFiles = files.filter(file => 
        file.startsWith('summary_') && file.endsWith('.json')
      );

      console.log(`📁 Found ${summaryFiles.length} summary files`);

      const summaries: MeetingSummary[] = [];
      
      // 並列処理で高速化
      const summaryPromises = summaryFiles.map(async (file) => {
        try {
          const filePath = path.join(this.dataDir, file);
          const content = await fs.readFile(filePath, 'utf-8');
          const summary: MeetingSummary = JSON.parse(content);
          
          // データ品質チェック
          if (!summary.meeting_info?.date || !summary.meeting_info?.house || !summary.meeting_info?.committee) {
            console.warn(`⚠️ Invalid summary data in ${file}`);
            return null;
          }
          
          return summary;
        } catch (error) {
          console.error(`❌ Error loading summary file ${file}:`, error);
          return null;
        }
      });

      const loadedSummaries = await Promise.all(summaryPromises);
      
      // null値を除外
      loadedSummaries.forEach(summary => {
        if (summary) {
          summaries.push(summary);
        }
      });

      // 日付順にソート（新しい順）
      summaries.sort((a, b) => 
        new Date(b.meeting_info.date).getTime() - new Date(a.meeting_info.date).getTime()
      );

      console.log(`✅ Successfully loaded ${summaries.length} summaries (${summaries.length > 0 ? summaries[0].meeting_info.date : 'N/A'} ~ ${summaries.length > 0 ? summaries[summaries.length - 1].meeting_info.date : 'N/A'})`);

      // キャッシュに保存
      SummariesLoader.cache.set(cacheKey, {
        data: summaries,
        timestamp: Date.now()
      });

      return summaries;
    } catch (error) {
      console.error('❌ Error loading summaries:', error);
      return [];
    }
  }

  /**
   * 要約検索
   */
  async searchSummaries(params: SummarySearchParams): Promise<SummariesResult> {
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
  async getAvailableHouses(): Promise<string[]> {
    const summaries = await this.loadAllSummaries();
    const houses = new Set(summaries.map(s => s.meeting_info.house));
    return Array.from(houses).sort();
  }

  /**
   * 利用可能な委員会の一覧を取得
   */
  async getAvailableCommittees(): Promise<string[]> {
    const summaries = await this.loadAllSummaries();
    const committees = new Set(summaries.map(s => s.meeting_info.committee));
    return Array.from(committees).sort();
  }

  /**
   * 利用可能なキーワードの一覧を取得
   */
  async getAvailableKeywords(): Promise<string[]> {
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
  async getSummaryStats() {
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