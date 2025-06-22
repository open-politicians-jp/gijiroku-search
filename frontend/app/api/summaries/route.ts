import { NextRequest, NextResponse } from 'next/server';
import { SummariesLoader } from '@/lib/summaries-loader';
import { SummarySearchParams } from '@/types';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    
    const params: SummarySearchParams = {
      q: searchParams.get('q') || undefined,
      house: searchParams.get('house') || undefined,
      committee: searchParams.get('committee') || undefined,
      date_from: searchParams.get('date_from') || undefined,
      date_to: searchParams.get('date_to') || undefined,
      keywords: searchParams.get('keywords')?.split(',').filter(Boolean) || undefined,
      limit: parseInt(searchParams.get('limit') || '10'),
      offset: parseInt(searchParams.get('offset') || '0'),
    };

    const loader = new SummariesLoader();
    const result = await loader.searchSummaries(params);

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in summaries API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}