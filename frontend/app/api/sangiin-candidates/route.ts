import { NextRequest, NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';

interface SangiinCandidate {
  candidate_id: string;
  name: string;
  name_kana?: string;
  prefecture: string;
  constituency: string;
  constituency_type: string;
  party: string;
  party_normalized: string;
  profile_url?: string;
  source_page: string;
  source: string;
  collected_at: string;
}

interface SangiinCandidatesData {
  metadata: {
    data_type: string;
    collection_method: string;
    total_candidates: number;
    candidates_with_kana: number;
    successful_prefectures: number;
    failed_prefectures: number;
    generated_at: string;
    source_site: string;
    coverage: {
      constituency_types: number;
      parties: number;
      prefectures: number;
    };
  };
  statistics: {
    by_party: Record<string, number>;
    by_prefecture: Record<string, number>;
    by_constituency_type: Record<string, number>;
  };
  data: SangiinCandidate[];
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // クエリパラメータ取得
    const query = searchParams.get('q') || '';
    const party = searchParams.get('party') || '';
    const prefecture = searchParams.get('prefecture') || '';
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');

    // データファイル読み込み
    const dataPath = join(process.cwd(), 'public', 'data', 'sangiin_candidates', 'go2senkyo_optimized_latest.json');
    const rawData = readFileSync(dataPath, 'utf-8');
    const candidatesData: SangiinCandidatesData = JSON.parse(rawData);
    
    let candidates = candidatesData.data;

    // フィルタリング
    if (query) {
      const queryLower = query.toLowerCase();
      candidates = candidates.filter(candidate => {
        const name = candidate.name.toLowerCase();
        const nameKana = candidate.name_kana?.toLowerCase() || '';
        const candidateParty = candidate.party.toLowerCase();
        const candidatePrefecture = candidate.prefecture.toLowerCase();
        
        // 政党名は完全一致または前方一致
        const partyMatch = candidateParty === queryLower || candidateParty.startsWith(queryLower);
        
        // その他は部分一致
        const otherMatch = name.includes(queryLower) ||
                          nameKana.includes(queryLower) ||
                          candidatePrefecture.includes(queryLower);
        
        return partyMatch || otherMatch;
      });
    }

    if (party) {
      candidates = candidates.filter(candidate => candidate.party === party);
    }

    if (prefecture) {
      candidates = candidates.filter(candidate => candidate.prefecture === prefecture);
    }

    // ページネーション
    const total = candidates.length;
    const paginatedCandidates = candidates.slice(offset, offset + limit);

    // レスポンス
    return NextResponse.json({
      success: true,
      data: paginatedCandidates,
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total
      },
      filters: {
        query: query || null,
        party: party || null,
        prefecture: prefecture || null
      },
      metadata: candidatesData.metadata,
      statistics: candidatesData.statistics
    });

  } catch (error) {
    console.error('参議院選候補者データ取得エラー:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: '参議院選候補者データの取得に失敗しました',
        data: [],
        pagination: { total: 0, limit: 0, offset: 0, hasMore: false }
      },
      { status: 500 }
    );
  }
}

// 統計情報のみ取得するエンドポイント
export async function HEAD(request: NextRequest) {
  try {
    const dataPath = join(process.cwd(), 'public', 'data', 'sangiin_candidates', 'go2senkyo_optimized_latest.json');
    const rawData = readFileSync(dataPath, 'utf-8');
    const candidatesData: SangiinCandidatesData = JSON.parse(rawData);
    
    return NextResponse.json({
      success: true,
      metadata: candidatesData.metadata,
      statistics: candidatesData.statistics
    });

  } catch (error) {
    console.error('参議院選候補者統計取得エラー:', error);
    return NextResponse.json(
      { success: false, error: '統計情報の取得に失敗しました' },
      { status: 500 }
    );
  }
}