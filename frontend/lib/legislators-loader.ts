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
      if (this.cache.metadata?.total_count && this.cache.metadata.total_count > 0) {
        return this.cache;
      }
      // 総数0の場合は再取得を試みる（データ切替直後の反映目的）
    }

    try {
      // 参議院（最新データ）
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
    const basePath = process.env.NODE_ENV === 'production' ? '/gijiroku-search' : '';
    
    // 試行するファイルパス（最新エイリアス → 新しい候補 → 既存候補）
    const possiblePaths = [
      `${basePath}/data/legislators/sangiin_legislators_latest.json`,
      `${basePath}/data/legislators/legislators_latest.json`,
      `${basePath}/data/legislators/legislators_20250721_000000.json`,
      `${basePath}/data/legislators/legislators_20250601_120005.json`,
      `${basePath}/data/legislators/legislators_20250601_120004.json`,
      `${basePath}/data/legislators/sangiin_legislators_unified_20250621_002031.json`,
      `${basePath}/data/legislators/sangiin_legislators_unified_20250621_001253.json`
    ];

    for (const dataPath of possiblePaths) {
      try {
        const response = await fetch(dataPath);
        if (response.ok) {
          const jsonData = await response.json();
          const rawList = Array.isArray(jsonData)
            ? jsonData
            : (jsonData.data || jsonData.legislators || []);
          return this.normalizeJsonLegislators(rawList);
        }
      } catch (error) {
        // 最後のファイルの場合のみエラーログを出力
        if (dataPath === possiblePaths[possiblePaths.length - 1]) {
          console.error('議員データの読み込みに失敗しました', error);
        }
        continue;
      }
    }

    console.error('全ての議員データファイルの読み込みに失敗しました');
    return [];
  }

  /**
   * アーカイブ: 2025/07/21 参議院選までの議員データ（参議院）
   * 既存の旧データ候補から読み込み、LegislatorsData 形式で返す
   */
  async loadArchivedSangiinLegislators_20250720(): Promise<LegislatorsData> {
    const basePath = process.env.NODE_ENV === 'production' ? '/gijiroku-search' : '';
    const archivePaths = [
      // 新アーカイブ配置（YYYYMMDD配下）
      `${basePath}/data/legislators/archive/20250720/sangiin_legislators.json`,
      // 既存の保存版名称
      `${basePath}/data/legislators/sangiin_legislators_until_20250720.json`,
      // 旧候補
      `${basePath}/data/legislators/legislators_20250601_120005.json`,
      `${basePath}/data/legislators/legislators_20250601_120004.json`,
      `${basePath}/data/legislators/sangiin_legislators_unified_20250621_002031.json`,
      `${basePath}/data/legislators/sangiin_legislators_unified_20250621_001253.json`
    ];

    for (const dataPath of archivePaths) {
      try {
        const response = await fetch(dataPath);
        if (response.ok) {
          const jsonData = await response.json();
          const rawList = Array.isArray(jsonData)
            ? jsonData
            : (jsonData.data || jsonData.legislators || []);
          const sangiin = this.normalizeJsonLegislators(rawList);
          const data: LegislatorsData = {
            metadata: {
              total_count: sangiin.length,
              last_updated: new Date().toISOString(),
              data_source: 'archive_sangiin_until_2025-07-20',
              sangiin_count: sangiin.length,
              shugiin_count: 0,
            },
            data: sangiin,
          };
          return data;
        }
      } catch (error) {
        continue;
      }
    }

    // フォールバック（空）
    return {
      metadata: {
        total_count: 0,
        last_updated: new Date().toISOString(),
        data_source: 'archive_sangiin_until_2025-07-20_not_found',
        sangiin_count: 0,
        shugiin_count: 0,
      },
      data: [],
    };
  }

  /**
   * 任意日付のアーカイブ（例: '20250720'）を読み込み
   */
  async loadArchivedSangiinLegislators(date: string = '20250720'): Promise<LegislatorsData> {
    const basePath = process.env.NODE_ENV === 'production' ? '/gijiroku-search' : '';
    const archivePaths = [
      `${basePath}/data/legislators/archive/${date}/sangiin_legislators.json`,
      // 固定の保存版名称（互換）
      `${basePath}/data/legislators/sangiin_legislators_until_20250720.json`,
    ];

    for (const dataPath of archivePaths) {
      try {
        const response = await fetch(dataPath);
        if (response.ok) {
          const jsonData = await response.json();
          const rawList = Array.isArray(jsonData)
            ? jsonData
            : (jsonData.data || jsonData.legislators || []);
          const sangiin = this.normalizeJsonLegislators(rawList);
          return {
            metadata: {
              total_count: sangiin.length,
              last_updated: new Date().toISOString(),
              data_source: `archive_sangiin_${date}`,
              sangiin_count: sangiin.length,
              shugiin_count: 0,
            },
            data: sangiin,
          };
        }
      } catch (error) {
        continue;
      }
    }

    return {
      metadata: {
        total_count: 0,
        last_updated: new Date().toISOString(),
        data_source: `archive_sangiin_${date}_not_found` ,
        sangiin_count: 0,
        shugiin_count: 0,
      },
      data: [],
    };
  }

  /**
   * 衆議院アーカイブデータを読み込み（解散前データ等）
   */
  async loadArchivedShugiinLegislators(date: string = '20261226_pre_dissolution'): Promise<LegislatorsData> {
    const basePath = process.env.NODE_ENV === 'production' ? '/gijiroku-search' : '';
    const archivePaths = [
      `${basePath}/data/legislators/archive/${date}/shugiin_legislators_pre_dissolution.json`,
      `${basePath}/data/legislators/archive/${date}/shugiin_legislators.json`,
    ];

    for (const dataPath of archivePaths) {
      try {
        const response = await fetch(dataPath);
        if (response.ok) {
          const jsonData = await response.json();
          const rawList = Array.isArray(jsonData)
            ? jsonData
            : (jsonData.data || jsonData.legislators || []);
          const shugiin = this.normalizeJsonLegislators(rawList).map((leg) => ({
            ...leg,
            house: 'shugiin' as const,
          }));
          return {
            metadata: {
              total_count: shugiin.length,
              last_updated: new Date().toISOString(),
              data_source: `archive_shugiin_${date}`,
              sangiin_count: 0,
              shugiin_count: shugiin.length,
            },
            data: shugiin,
          };
        }
      } catch (error) {
        continue;
      }
    }

    return {
      metadata: {
        total_count: 0,
        last_updated: new Date().toISOString(),
        data_source: `archive_shugiin_${date}_not_found`,
        sangiin_count: 0,
        shugiin_count: 0,
      },
      data: [],
    };
  }

  /**
   * 汎用アーカイブデータ読み込み（house指定対応）
   */
  async loadArchivedLegislators(date: string, house?: 'shugiin' | 'sangiin'): Promise<LegislatorsData> {
    if (house === 'shugiin') {
      return this.loadArchivedShugiinLegislators(date);
    } else if (house === 'sangiin') {
      return this.loadArchivedSangiinLegislators(date);
    }
    // house未指定の場合は参議院（互換性維持）
    return this.loadArchivedSangiinLegislators(date);
  }

  /**
   * 衆議院データを読み込み（将来実装予定）
   */
  private async loadShugiinData(): Promise<Legislator[]> {
    try {
      const basePath = process.env.NODE_ENV === 'production' ? '/gijiroku-search' : '';
      const candidates = [
        `${basePath}/data/legislators/shugiin_legislators_latest.json`,
        `${basePath}/data/legislators/legislators_latest.json`,
        `${basePath}/data/legislators/legislators_20251101_210546.json`,
      ];

      for (const dataPath of candidates) {
        try {
          const response = await fetch(dataPath);
          if (!response.ok) continue;
          const jsonData = await response.json();
          const rawList = Array.isArray(jsonData)
            ? jsonData
            : (jsonData.data || jsonData.legislators || []);
          if (rawList.length === 0) continue;
          const normalized = this.normalizeJsonLegislators(rawList).map((leg) => ({
            ...leg,
            house: 'shugiin' as const,
          }));
          return normalized;
        } catch (error) {
          // 次の候補へ
          continue;
        }
      }

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
    return jsonLegislators.map((leg, index) => {
      // 柔軟なフィールド対応
      const name = leg.name || leg.name_kanji || leg.common_name || leg.legal_name || '';
      const rawHouse = leg.house || '';
      const houseMapped = rawHouse === '参議院' ? 'sangiin' : rawHouse === '衆議院' ? 'shugiin' : (rawHouse as 'sangiin' | 'shugiin');
      const party = leg.party_normalized || leg.party || '';
      const profileUrl = leg.profile_url || leg.profile || '';
      const photoUrl = leg.photo_url || '';
      const termEnd = leg.term_end || '';
      const positions = leg.positions || '';
      // 初当選年の推定が無い場合は現年を設定
      const electionYear = leg.first_election_year || new Date().getFullYear();

      return {
        id: String(leg.id ?? `leg_${index}`),
        name,
        house: (houseMapped || 'sangiin') as 'shugiin' | 'sangiin',
        party,
        constituency: leg.constituency || '',
        electionYear,
        status: (leg.status as 'active' | 'inactive') || 'active',
        region: leg.region || undefined,
        termCount: leg.term_count,
        termEnd,
        positions,
        profileUrl,
        photoUrl,
        wikipediaUrl: leg.wikipedia?.url,
        wikipediaTitle: leg.wikipedia?.title,
        wikipediaSummary: leg.wikipedia?.summary,
        personalWebsite: leg.personal_website?.url,
        personalWebsiteTitle: leg.personal_website?.title,
        snsAccounts: leg.sns_accounts || {},
        openpoliticsUrl: leg.openpolitics_url,
        detailsEnhancedAt: leg.details_enhanced_at,
        otherLinks: leg.other_links || [],
      } as Legislator;
    });
  }

  /**
   * フォールバック用モックデータ読み込み
   */
  private async loadFallbackData(): Promise<LegislatorsData> {
    try {
      // GitHub Pages対応のパス設定
      const basePath = process.env.NODE_ENV === 'production' ? '/gijiroku-search' : '';
      const csvPath = `${basePath}/data/legislators/legislators_mock.csv`;
      
      const response = await fetch(csvPath);
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
