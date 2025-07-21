import { NextRequest, NextResponse } from 'next/server';
import { Env, CommitteeNewsRecord } from '@/types/cloudflare';

/// <reference types="@cloudflare/workers-types" />
interface CloudflareRequest extends NextRequest {
  env: Env;
}

export async function GET(request: CloudflareRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q') || '';
    const committee = searchParams.get('committee') || '';
    const dateFrom = searchParams.get('dateFrom') || '';
    const dateTo = searchParams.get('dateTo') || '';
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    // クエリ条件の構築
    const conditions: string[] = [];
    const params: any[] = [];

    if (query) {
      conditions.push('(title LIKE ? OR content LIKE ?)');
      params.push(`%${query}%`, `%${query}%`);
    }

    if (committee) {
      conditions.push('committee = ?');
      params.push(committee);
    }

    if (dateFrom) {
      conditions.push('date >= ?');
      params.push(dateFrom);
    }

    if (dateTo) {
      conditions.push('date <= ?');
      params.push(dateTo);
    }

    // SQLクエリの構築
    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const searchQuery = `
      SELECT * FROM committee_news 
      ${whereClause}
      ORDER BY date DESC, created_at DESC
      LIMIT ? OFFSET ?
    `;

    params.push(limit, offset);

    // D1データベースクエリ実行
    const result = await request.env.DB.prepare(searchQuery).bind(...params).all<CommitteeNewsRecord>();

    if (!result.success) {
      throw new Error(result.error || 'データベースクエリエラー');
    }

    // 総件数の取得
    const countQuery = `
      SELECT COUNT(*) as total FROM committee_news 
      ${whereClause}
    `;
    const countParams = params.slice(0, -2); // limit, offsetを除く
    const countResult = await request.env.DB.prepare(countQuery).bind(...countParams).first<{ total: number }>();

    const total = countResult?.total || 0;

    // 委員会別統計
    const committeeStatsQuery = `
      SELECT 
        committee,
        COUNT(*) as news_count,
        MAX(date) as latest_news,
        MIN(date) as earliest_news
      FROM committee_news
      GROUP BY committee
      ORDER BY news_count DESC
    `;
    const committeeStats = await request.env.DB.prepare(committeeStatsQuery).all();

    // 月別統計（過去6ヶ月）
    const monthlyStatsQuery = `
      SELECT 
        substr(date, 1, 7) as month,
        COUNT(*) as news_count,
        COUNT(DISTINCT committee) as active_committees
      FROM committee_news
      WHERE date >= date('now', '-6 months')
      GROUP BY substr(date, 1, 7)
      ORDER BY month DESC
    `;
    const monthlyStats = await request.env.DB.prepare(monthlyStatsQuery).all();

    // 最近の活動（過去7日）
    const recentActivityQuery = `
      SELECT 
        committee,
        COUNT(*) as recent_news
      FROM committee_news
      WHERE date >= date('now', '-7 days')
      GROUP BY committee
      ORDER BY recent_news DESC
      LIMIT 10
    `;
    const recentActivity = await request.env.DB.prepare(recentActivityQuery).all();

    return NextResponse.json({
      success: true,
      data: result.results,
      meta: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total,
        query: {
          q: query,
          committee,
          dateFrom,
          dateTo
        },
        stats: {
          committees: committeeStats.results,
          monthly: monthlyStats.results,
          recent_activity: recentActivity.results
        }
      }
    });

  } catch (error) {
    console.error('委員会ニュースAPIエラー:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '委員会ニュースデータの取得に失敗しました',
        data: []
      },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}