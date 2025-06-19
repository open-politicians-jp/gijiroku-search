/**
 * 議員リンク生成システム
 * 
 * 発言者名から議員プロフィールページへのリンクを生成
 * 選挙による変更に対応した柔軟なマッチングシステム
 */

interface LegislatorProfile {
  name: string;
  house: string;
  district: string;
  party: string;
  party_normalized: string;
  profile_url: string;
  year: number;
  source: string;
}

interface LegislatorsData {
  metadata: {
    year: number;
    total_legislators: number;
    shugiin_count: number;
    sangiin_count: number;
  };
  party_statistics: any;
  data: {
    shugiin: LegislatorProfile[];
    sangiin: LegislatorProfile[];
  };
}

class LegislatorsLinker {
  private legislatorsData: LegislatorsData | null = null;
  private lastLoadTime: number = 0;
  private readonly CACHE_DURATION = 30 * 60 * 1000; // 30分キャッシュ
  
  /**
   * 議員データを読み込み
   */
  async loadLegislatorsData(): Promise<boolean> {
    const now = Date.now();
    
    if (this.legislatorsData && (now - this.lastLoadTime) < this.CACHE_DURATION) {
      return true;
    }

    try {
      const currentYear = new Date().getFullYear();
      const response = await fetch(`/data/legislators/legislators_${currentYear}_latest.json`);
      
      if (!response.ok) {
        // 前年のデータを試行
        const fallbackResponse = await fetch(`/data/legislators/legislators_${currentYear - 1}_latest.json`);
        if (!fallbackResponse.ok) {
          throw new Error('議員データが見つかりません');
        }
        this.legislatorsData = await fallbackResponse.json();
      } else {
        this.legislatorsData = await response.json();
      }
      
      this.lastLoadTime = now;
      return true;
    } catch (error) {
      console.error('議員データ読み込みエラー:', error);
      return false;
    }
  }

  /**
   * 発言者名から議員プロフィールを検索
   */
  findLegislatorByName(speakerName: string): LegislatorProfile | null {
    if (!this.legislatorsData) {
      return null;
    }

    const allLegislators = [
      ...this.legislatorsData.data.shugiin,
      ...this.legislatorsData.data.sangiin
    ];

    // 1. 完全一致検索
    let match = allLegislators.find(legislator => 
      legislator.name === speakerName
    );

    if (match) {
      return match;
    }

    // 2. 部分一致検索（姓のみ、名のみ）
    const speakerParts = this.splitName(speakerName);
    
    for (const legislator of allLegislators) {
      const legislatorParts = this.splitName(legislator.name);
      
      // 姓が一致する場合
      if (speakerParts.lastName && legislatorParts.lastName &&
          speakerParts.lastName === legislatorParts.lastName) {
        
        // 名も一致するかチェック
        if (speakerParts.firstName && legislatorParts.firstName) {
          if (speakerParts.firstName === legislatorParts.firstName) {
            return legislator;
          }
        } else {
          // 姓のみの一致でも候補として返す
          match = legislator;
        }
      }
    }

    return match || null;
  }

  /**
   * 名前を姓と名に分割
   */
  private splitName(fullName: string): { lastName: string; firstName: string } {
    // 日本人名の一般的なパターンに対応
    const trimmed = fullName.trim();
    
    // スペースで分割
    if (trimmed.includes(' ')) {
      const parts = trimmed.split(' ');
      return {
        lastName: parts[0],
        firstName: parts.slice(1).join(' ')
      };
    }
    
    // 2-4文字の姓を想定した分割
    if (trimmed.length >= 3) {
      // 一般的な日本人の姓の長さに基づく分割
      if (trimmed.length <= 4) {
        return {
          lastName: trimmed.substring(0, 2),
          firstName: trimmed.substring(2)
        };
      } else {
        // 長い名前の場合は3文字を姓と推定
        return {
          lastName: trimmed.substring(0, 3),
          firstName: trimmed.substring(3)
        };
      }
    }
    
    return {
      lastName: trimmed,
      firstName: ''
    };
  }

  /**
   * 議員情報から表示用リンクデータを生成
   */
  generateLegislatorLink(legislator: LegislatorProfile): {
    name: string;
    house: string;
    party: string;
    district: string;
    profileUrl: string;
  } {
    return {
      name: legislator.name,
      house: legislator.house,
      party: legislator.party_normalized || legislator.party,
      district: legislator.district,
      profileUrl: legislator.profile_url
    };
  }

  /**
   * 発言者名からリンク情報を生成
   */
  async generateSpeakerLink(speakerName: string): Promise<{
    name: string;
    isLinked: boolean;
    linkData?: {
      name: string;
      house: string;
      party: string;
      district: string;
      profileUrl: string;
    };
  }> {
    // 特殊な発言者は除外
    const excludedSpeakers = [
      '会議録情報',
      '議長',
      '委員長',
      '国務大臣',
      '政府参考人',
      '委員部'
    ];

    for (const excluded of excludedSpeakers) {
      if (speakerName.includes(excluded)) {
        return {
          name: speakerName,
          isLinked: false
        };
      }
    }

    // 議員データを読み込み
    const dataLoaded = await this.loadLegislatorsData();
    if (!dataLoaded) {
      return {
        name: speakerName,
        isLinked: false
      };
    }

    // 議員を検索
    const legislator = this.findLegislatorByName(speakerName);
    
    if (legislator) {
      return {
        name: speakerName,
        isLinked: true,
        linkData: this.generateLegislatorLink(legislator)
      };
    }

    return {
      name: speakerName,
      isLinked: false
    };
  }

  /**
   * 複数の発言者名を一括処理
   */
  async generateMultipleSpeakerLinks(speakerNames: string[]): Promise<Map<string, any>> {
    const dataLoaded = await this.loadLegislatorsData();
    const results = new Map();

    for (const speakerName of speakerNames) {
      const linkInfo = await this.generateSpeakerLink(speakerName);
      results.set(speakerName, linkInfo);
    }

    return results;
  }

  /**
   * 議員統計情報を取得
   */
  getLegislatorStatistics(): {
    totalLegislators: number;
    shugiinCount: number;
    sangiinCount: number;
    partyDistribution: Record<string, number>;
  } | null {
    if (!this.legislatorsData) {
      return null;
    }

    const allLegislators = [
      ...this.legislatorsData.data.shugiin,
      ...this.legislatorsData.data.sangiin
    ];

    const partyDistribution: Record<string, number> = {};
    
    for (const legislator of allLegislators) {
      const party = legislator.party_normalized || legislator.party;
      partyDistribution[party] = (partyDistribution[party] || 0) + 1;
    }

    return {
      totalLegislators: this.legislatorsData.metadata.total_legislators,
      shugiinCount: this.legislatorsData.metadata.shugiin_count,
      sangiinCount: this.legislatorsData.metadata.sangiin_count,
      partyDistribution
    };
  }
}

// シングルトンインスタンス
export const legislatorsLinker = new LegislatorsLinker();

// 便利な関数をエクスポート
export async function getSpeakerProfileLink(speakerName: string) {
  return await legislatorsLinker.generateSpeakerLink(speakerName);
}

export async function getLegislatorStatistics() {
  await legislatorsLinker.loadLegislatorsData();
  return legislatorsLinker.getLegislatorStatistics();
}