import { SearchParams, SearchResult, Stats } from '@/types';
import { dataLoader } from './data-loader';

export class APIClient {
  private useStaticLoader: boolean;
  private baseUrl: string;

  constructor() {
    // Cloudflare D1移行: API Routesを優先使用
    this.useStaticLoader = false;
    this.baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
    
    // 静的ローダーを明示的に使用する場合のフォールバック
    if (process.env.NEXT_PUBLIC_USE_STATIC_LOADER === 'true') {
      this.useStaticLoader = true;
    }
  }

  async search(params: SearchParams): Promise<SearchResult | any> {
    try {
      if (this.useStaticLoader) {
        // 静的データローダーを使用（フォールバック）
        return await dataLoader.search(params);
      }

      // D1 API routesを使用（GET メソッドでクエリパラメータ送信）
      const searchParams = new URLSearchParams();
      if (params.q) searchParams.set('q', params.q);
      if (params.speaker) searchParams.set('speaker', params.speaker);
      if (params.party) searchParams.set('party', params.party);
      if (params.committee) searchParams.set('committee', params.committee);
      if (params.house) searchParams.set('house', params.house);
      if (params.dateFrom) searchParams.set('dateFrom', params.dateFrom);
      if (params.dateTo) searchParams.set('dateTo', params.dateTo);
      if (params.limit) searchParams.set('limit', params.limit.toString());
      if (params.offset) searchParams.set('offset', params.offset.toString());

      const url = `${this.baseUrl}/api/search?${searchParams.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' })) as any;
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
        // 静的データローダーを使用（フォールバック）
        return await dataLoader.loadStats();
      }

      // D1 API routesを使用
      const url = `${this.baseUrl}/api/stats`;
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' })) as any;
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

      // D1 API routesを使用
      const searchParams = new URLSearchParams();
      if (params.q) searchParams.set('q', params.q);
      if (params.session) searchParams.set('session', params.session);
      if (params.house) searchParams.set('house', params.house);
      if (params.status) searchParams.set('status', params.status);
      if (params.dateFrom) searchParams.set('dateFrom', params.dateFrom);
      if (params.dateTo) searchParams.set('dateTo', params.dateTo);
      if (params.limit) searchParams.set('limit', params.limit.toString());
      if (params.offset) searchParams.set('offset', params.offset.toString());

      const url = `${this.baseUrl}/api/bills?${searchParams.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' })) as any;
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

      // D1 API routesを使用
      const searchParams = new URLSearchParams();
      if (params.q) searchParams.set('q', params.q);
      if (params.committee) searchParams.set('committee', params.committee);
      if (params.dateFrom) searchParams.set('dateFrom', params.dateFrom);
      if (params.dateTo) searchParams.set('dateTo', params.dateTo);
      if (params.limit) searchParams.set('limit', params.limit.toString());
      if (params.offset) searchParams.set('offset', params.offset.toString());

      const url = `${this.baseUrl}/api/committee-news?${searchParams.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' })) as any;
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

      // D1 API routesを使用
      const searchParams = new URLSearchParams();
      if (params.q) searchParams.set('q', params.q);
      if (params.questioner) searchParams.set('questioner', params.questioner);
      if (params.status) searchParams.set('status', params.status);
      if (params.dateFrom) searchParams.set('dateFrom', params.dateFrom);
      if (params.dateTo) searchParams.set('dateTo', params.dateTo);
      if (params.limit) searchParams.set('limit', params.limit.toString());
      if (params.offset) searchParams.set('offset', params.offset.toString());

      const url = `${this.baseUrl}/api/questions?${searchParams.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' })) as any;
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Questions search error:', error);
      throw new Error(`質問主意書検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }

  async searchManifestos(params: SearchParams) {
    try {
      if (this.useStaticLoader) {
        return await dataLoader.searchManifestos(params);
      }

      // D1 API routesを使用
      const searchParams = new URLSearchParams();
      if (params.party) searchParams.set('party', params.party);
      if (params.format) searchParams.set('format', params.format);

      const url = `${this.baseUrl}/api/manifestos?${searchParams.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' })) as any;
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Manifestos search error:', error);
      throw new Error(`マニフェスト検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  }
}

export const apiClient = new APIClient();