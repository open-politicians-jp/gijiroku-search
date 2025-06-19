import { SearchParams, SearchResult, Stats } from '@/types';
import { dataLoader } from './data-loader';

export class APIClient {
  async search(params: SearchParams): Promise<SearchResult | any> {
    try {
      // 静的データローダーを使用（SPA対応）
      return await dataLoader.search(params);
    } catch (error) {
      console.error('Search error:', error);
      throw new Error(`検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }

  async getStats(): Promise<Stats> {
    try {
      // 静的データローダーを使用（SPA対応）
      return await dataLoader.loadStats();
    } catch (error) {
      console.error('Stats error:', error);
      throw new Error(`統計情報の取得に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }
}

export const apiClient = new APIClient();