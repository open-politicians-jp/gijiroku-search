import { NextRequest, NextResponse } from 'next/server';
import { dataLoader } from '@/lib/data-loader';
import { SearchParams } from '@/types';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // URLパラメータを解析
    const params: SearchParams = {
      q: searchParams.get('q') || undefined,
      speaker: searchParams.get('speaker') || undefined,
      party: searchParams.get('party') || undefined,
      committee: searchParams.get('committee') || undefined,
      date_from: searchParams.get('date_from') || undefined,
      date_to: searchParams.get('date_to') || undefined,
      search_type: (searchParams.get('search_type') as 'speeches' | 'committee_news' | 'bills' | 'questions') || 'speeches',
      limit: searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : undefined,
      offset: searchParams.get('offset') ? parseInt(searchParams.get('offset')!) : undefined,
    };

    // データローダーを使用して検索実行
    const result = await dataLoader.search(params);

    return NextResponse.json(result, {
      headers: {
        'Cache-Control': 'public, max-age=300, stale-while-revalidate=600',
      },
    });
  } catch (error) {
    console.error('Search API error:', error);
    return NextResponse.json(
      { error: `検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}` },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const params: SearchParams = await request.json();
    
    // データローダーを使用して検索実行
    const result = await dataLoader.search(params);

    return NextResponse.json(result, {
      headers: {
        'Cache-Control': 'public, max-age=300, stale-while-revalidate=600',
      },
    });
  } catch (error) {
    console.error('Search API POST error:', error);
    return NextResponse.json(
      { error: `検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}` },
      { status: 500 }
    );
  }
}