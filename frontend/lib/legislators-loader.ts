import { Legislator, LegislatorsData, LegislatorFilter } from '@/types/legislator';

class LegislatorsLoader {
  private cache: LegislatorsData | null = null;
  private cacheTimestamp: number = 0;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  /**
   * JSONファイル形式の議員データを読み込み（参議院・衆議院対応）
   */
  async loadLegislators(): Promise<LegislatorsData> {
    // キャッシュチェック
    if (this.cache && Date.now() - this.cacheTimestamp < this.CACHE_DURATION) {
      return this.cache;
    }

    try {
      // 参議院データの統合ファイルを読み込み
      const sangiinData = await this.loadSangiinData();
      
      // 衆議院データ（将来追加予定）
      const shugiinData = await this.loadShugiinData();
      
      // データ統合
      const allLegislators = [...sangiinData, ...shugiinData];

      const data: LegislatorsData = {
        metadata: {
          total_count: allLegislators.length,
          last_updated: new Date().toISOString(),
          data_source: 'real_json_data',
          sangiin_count: sangiinData.length,
          shugiin_count: shugiinData.length,
        },
        data: allLegislators,
      };

      // キャッシュ更新
      this.cache = data;
      this.cacheTimestamp = Date.now();

      return data;
    } catch (error) {
      console.error('Error loading legislators data:', error);
      // フォールバック: モックCSVデータを使用
      return await this.loadFallbackData();
    }
  }

  /**
   * 参議院データを読み込み
   */
  private async loadSangiinData(): Promise<Legislator[]> {
    try {
      // 最新の統合ファイルを取得
      const response = await fetch('/data/legislators/sangiin_legislators_unified_20250621_002031.json');
      if (!response.ok) {
        throw new Error(`Failed to fetch sangiin data: ${response.status}`);
      }

      const jsonData = await response.json();
      return this.normalizeJsonLegislators(jsonData.data);
    } catch (error) {
      console.warn('Failed to load sangiin data:', error);
      return [];
    }
  }

  /**
   * 衆議院データを読み込み（将来実装予定）
   */
  private async loadShugiinData(): Promise<Legislator[]> {
    try {
      // 衆議院データが追加されたら実装
      // const response = await fetch('/data/legislators/shugiin_legislators_unified.json');
      // if (response.ok) {
      //   const jsonData = await response.json();
      //   return this.normalizeJsonLegislators(jsonData.data);
      // }
      return [];
    } catch (error) {
      console.warn('Shugiin data not available yet:', error);
      return [];
    }
  }

  /**
   * JSONデータを内部形式に正規化
   */
  private normalizeJsonLegislators(jsonLegislators: any[]): Legislator[] {
    return jsonLegislators.map((leg, index) => ({
      id: leg.id || `leg_${index}`,
      name: leg.name || '',
      house: leg.house as 'shugiin' | 'sangiin',
      party: leg.party || '',
      constituency: leg.constituency || '',
      electionYear: leg.first_election_year || new Date().getFullYear(),
      status: leg.status as 'active' | 'inactive' || 'active',
      region: leg.region || undefined,
      // 追加フィールド
      termCount: leg.term_count,
      termEnd: leg.term_end,
      positions: leg.positions,
      profileUrl: leg.profile_url,
      photoUrl: leg.photo_url,
    }));
  }

  /**
   * フォールバック用モックデータ読み込み
   */
  private async loadFallbackData(): Promise<LegislatorsData> {
    try {
      const response = await fetch('/data/legislators/legislators_mock.csv');
      if (!response.ok) {
        throw new Error(`Failed to fetch fallback data: ${response.status}`);
      }

      const csvText = await response.text();
      const legislators = this.parseCSV(csvText);

      return {
        metadata: {
          total_count: legislators.length,
          last_updated: new Date().toISOString(),
          data_source: 'fallback_csv_data',
        },
        data: legislators,
      };
    } catch (error) {
      console.error('Fallback data also failed:', error);
      return {
        metadata: {
          total_count: 0,
          last_updated: new Date().toISOString(),
          data_source: 'empty_fallback',
        },
        data: [],
      };
    }
  }

  /**
   * CSVテキストをLegislator配列に変換
   */
  private parseCSV(csvText: string): Legislator[] {
    const lines = csvText.trim().split('\n');
    const header = lines[0].split(',');
    
    return lines.slice(1).map((line, index) => {
      const values = this.parseCSVLine(line);
      const row: Record<string, string> = {};
      
      header.forEach((key, i) => {
        row[key.trim()] = values[i]?.trim() || '';
      });

      return {
        id: row.id || String(index + 1),
        name: row.name || '',
        house: (row.house === 'shugiin' || row.house === 'sangiin') ? row.house : 'shugiin',
        party: row.party || '',
        constituency: row.constituency || '',
        electionYear: parseInt(row.electionYear) || new Date().getFullYear(),
        status: (row.status === 'active' || row.status === 'inactive') ? row.status : 'active',
        region: row.region || undefined,
      } as Legislator;
    }).filter(legislator => legislator.name); // 名前がないエントリを除外
  }

  /**
   * CSVの1行をパース（カンマ区切り、クォート対応）
   */
  private parseCSVLine(line: string): string[] {
    const values: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    
    values.push(current);
    return values;
  }

  /**
   * 議員リストをフィルタリング
   */
  filterLegislators(legislators: Legislator[], filter: LegislatorFilter): Legislator[] {
    return legislators.filter(legislator => {
      // 院別フィルター
      if (filter.house && filter.house !== 'all' && legislator.house !== filter.house) {
        return false;
      }

      // 政党フィルター
      if (filter.party && filter.party !== 'all' && legislator.party !== filter.party) {
        return false;
      }

      // ステータスフィルター
      if (filter.status && filter.status !== 'all' && legislator.status !== filter.status) {
        return false;
      }

      // 検索フィルター
      if (filter.search) {
        const searchLower = filter.search.toLowerCase();
        const searchTargets = [
          legislator.name,
          legislator.party,
          legislator.constituency,
          legislator.region || '',
        ].join(' ').toLowerCase();
        
        if (!searchTargets.includes(searchLower)) {
          return false;
        }
      }

      return true;
    });
  }

  /**
   * ユニークな政党リストを取得
   */
  async getUniqueParties(): Promise<string[]> {
    const data = await this.loadLegislators();
    const partiesSet = new Set(data.data.map(l => l.party));
    const parties = Array.from(partiesSet).filter(Boolean);
    return parties.sort();
  }

  /**
   * 院別の議員数を取得
   */
  async getHouseCounts(): Promise<{ shugiin: number; sangiin: number; total: number }> {
    const data = await this.loadLegislators();
    const shugiinCount = data.data.filter(l => l.house === 'shugiin').length;
    const sangiinCount = data.data.filter(l => l.house === 'sangiin').length;
    
    return {
      shugiin: shugiinCount,
      sangiin: sangiinCount,
      total: shugiinCount + sangiinCount,
    };
  }
}

// シングルトンインスタンス
export const legislatorsLoader = new LegislatorsLoader();