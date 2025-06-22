import { MeetingSummary, SummarySearchParams, SummariesResult } from '@/types';
import { promises as fs } from 'fs';
import path from 'path';

/**
 * 議会要約データローダー
 */
export class SummariesLoader {
  private dataDir: string;

  constructor() {
    this.dataDir = path.join(process.cwd(), 'public', 'data', 'summaries');
  }

  /**
   * 全ての要約ファイルを読み込み
   */
  async loadAllSummaries(): Promise<MeetingSummary[]> {
    try {
      const files = await fs.readdir(this.dataDir);
      const summaryFiles = files.filter(file => 
        file.startsWith('summary_') && file.endsWith('.json')
      );

      const summaries: MeetingSummary[] = [];
      
      for (const file of summaryFiles) {
        try {
          const filePath = path.join(this.dataDir, file);
          const content = await fs.readFile(filePath, 'utf-8');
          const summary: MeetingSummary = JSON.parse(content);
          summaries.push(summary);
        } catch (error) {
          console.error(`Error loading summary file ${file}:`, error);
        }
      }

      // 日付順にソート（新しい順）
      summaries.sort((a, b) => 
        new Date(b.meeting_info.date).getTime() - new Date(a.meeting_info.date).getTime()
      );

      return summaries;
    } catch (error) {
      console.error('Error loading summaries:', error);
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