import { SearchParams, SearchResult, Stats } from '@/types';
import { dataLoader } from './data-loader';

export class APIClient {
  private useStaticLoader: boolean;

  constructor() {
    // GitHub Pages等の静的サイトでは静的ローダーを使用
    // API routesが利用可能な環境では API を使用
    this.useStaticLoader = process.env.NEXT_PUBLIC_USE_STATIC_LOADER === 'true' || 
                          typeof window !== 'undefined' && window.location.hostname.includes('github.io');
  }

  async search(params: SearchParams): Promise<SearchResult | any> {
    try {
      if (this.useStaticLoader) {
        // 静的データローダーを使用（GitHub Pages等）
        return await dataLoader.search(params);
      }

      // API routesを使用
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Search error:', error);
      throw new Error(`検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }

  async getStats(): Promise<Stats> {
    try {
      if (this.useStaticLoader) {
        // 静的データローダーを使用（GitHub Pages等）
        return await dataLoader.loadStats();
      }

      // API routesを使用
      const response = await fetch('/api/stats');

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Stats error:', error);
      throw new Error(`統計情報の取得に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }

  async searchBills(params: SearchParams) {
    try {
      if (this.useStaticLoader) {
        return await dataLoader.searchBills(params);
      }

      const response = await fetch('/api/bills', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Bills search error:', error);
      throw new Error(`法案検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }

  async searchCommitteeNews(params: SearchParams) {
    try {
      if (this.useStaticLoader) {
        return await dataLoader.searchCommitteeNews(params);
      }

      const response = await fetch('/api/committee-news', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Committee news search error:', error);
      throw new Error(`委員会ニュース検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }

  async searchQuestions(params: SearchParams) {
    try {
      if (this.useStaticLoader) {
        return await dataLoader.searchQuestions(params);
      }

      const response = await fetch('/api/questions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Questions search error:', error);
      throw new Error(`質問主意書検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }
}

export const apiClient = new APIClient();