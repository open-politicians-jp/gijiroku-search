import { NextRequest, NextResponse } from 'next/server';
import { Env, BillRecord } from '@/types/cloudflare';

/// <reference types="@cloudflare/workers-types" />
interface CloudflareRequest extends NextRequest {
  env: Env;
}

export async function GET(request: CloudflareRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q') || '';
    const session = searchParams.get('session') || '';
    const house = searchParams.get('house') || '';
    const status = searchParams.get('status') || '';
    const dateFrom = searchParams.get('dateFrom') || '';
    const dateTo = searchParams.get('dateTo') || '';
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    // クエリ条件の構築
    const conditions: string[] = [];
    const params: any[] = [];

    if (query) {
      conditions.push('(title LIKE ? OR bill_number LIKE ?)');
      params.push(`%${query}%`, `%${query}%`);
    }

    if (session) {
      conditions.push('session = ?');
      params.push(parseInt(session));
    }

    if (house) {
      conditions.push('house = ?');
      params.push(house);
    }

    if (status) {
      conditions.push('status = ?');
      params.push(status);
    }

    if (dateFrom) {
      conditions.push('submission_date >= ?');
      params.push(dateFrom);
    }

    if (dateTo) {
      conditions.push('submission_date <= ?');
      params.push(dateTo);
    }

    // SQLクエリの構築
    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const searchQuery = `
      SELECT * FROM bills 
      ${whereClause}
      ORDER BY submission_date DESC, session DESC, bill_number ASC
      LIMIT ? OFFSET ?
    `;

    params.push(limit, offset);

    // D1データベースクエリ実行
    const result = await request.env.DB.prepare(searchQuery).bind(...params).all<BillRecord>();

    if (!result.success) {
      throw new Error(result.error || 'データベースクエリエラー');
    }

    // 総件数の取得
    const countQuery = `
      SELECT COUNT(*) as total FROM bills 
      ${whereClause}
    `;
    const countParams = params.slice(0, -2); // limit, offsetを除く
    const countResult = await request.env.DB.prepare(countQuery).bind(...countParams).first<{ total: number }>();

    const total = countResult?.total || 0;

    // 会期別統計
    const sessionStatsQuery = `
      SELECT 
        session,
        house,
        COUNT(*) as bill_count,
        COUNT(DISTINCT status) as status_types
      FROM bills
      GROUP BY session, house
      ORDER BY session DESC, house
      LIMIT 10
    `;
    const sessionStats = await request.env.DB.prepare(sessionStatsQuery).all();

    // ステータス別統計
    const statusStatsQuery = `
      SELECT 
        status,
        COUNT(*) as count,
        COUNT(CASE WHEN house = '衆議院' THEN 1 END) as house_count,
        COUNT(CASE WHEN house = '参議院' THEN 1 END) as senate_count
      FROM bills
      GROUP BY status
      ORDER BY count DESC
    `;
    const statusStats = await request.env.DB.prepare(statusStatsQuery).all();

    // 最近の法案活動
    const recentActivityQuery = `
      SELECT 
        COUNT(*) as recent_bills,
        MIN(submission_date) as earliest_recent,
        MAX(submission_date) as latest_recent
      FROM bills
      WHERE submission_date >= date('now', '-30 days')
    `;
    const recentActivity = await request.env.DB.prepare(recentActivityQuery).first();

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
          session,
          house,
          status,
          dateFrom,
          dateTo
        },
        stats: {
          sessions: sessionStats.results,
          status: statusStats.results,
          recent_activity: recentActivity
        }
      }
    });

  } catch (error) {
    console.error('法案APIエラー:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '法案データの取得に失敗しました',
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