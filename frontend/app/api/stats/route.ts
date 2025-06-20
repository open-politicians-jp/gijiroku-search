import { NextResponse } from 'next/server';
import { dataLoader } from '@/lib/data-loader';

export async function GET() {
  try {
    // データローダーを使用して統計情報を取得
    const stats = await dataLoader.loadStats();

    return NextResponse.json(stats, {
      headers: {
        'Cache-Control': 'public, max-age=900, stale-while-revalidate=1800', // 15分キャッシュ
      },
    });
  } catch (error) {
    console.error('Stats API error:', error);
    return NextResponse.json(
      { error: `統計情報の取得に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}` },
      { status: 500 }
    );
  }
}