import { NextRequest, NextResponse } from 'next/server';
import { dataLoader } from '@/lib/data-loader';
import { SearchParams } from '@/types';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // URLパラメータを解析
    const params: SearchParams = {
      q: searchParams.get('q') || undefined,
      committee: searchParams.get('committee') || undefined,
      date_from: searchParams.get('date_from') || undefined,
      date_to: searchParams.get('date_to') || undefined,
      search_type: 'bills',
      limit: searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : 20,
      offset: searchParams.get('offset') ? parseInt(searchParams.get('offset')!) : 0,
    };

    // データローダーを使用して法案検索実行
    const result = await dataLoader.searchBills(params);

    return NextResponse.json(result, {
      headers: {
        'Cache-Control': 'public, max-age=300, stale-while-revalidate=600',
      },
    });
  } catch (error) {
    console.error('Bills API error:', error);
    return NextResponse.json(
      { error: `法案検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}` },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const params: SearchParams = await request.json();
    params.search_type = 'bills';
    
    // データローダーを使用して法案検索実行
    const result = await dataLoader.searchBills(params);

    return NextResponse.json(result, {
      headers: {
        'Cache-Control': 'public, max-age=300, stale-while-revalidate=600',
      },
    });
  } catch (error) {
    console.error('Bills API POST error:', error);
    return NextResponse.json(
      { error: `法案検索に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}` },
      { status: 500 }
    );
  }
}