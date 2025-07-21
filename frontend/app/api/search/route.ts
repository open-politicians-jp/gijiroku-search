import { NextRequest, NextResponse } from 'next/server';
import { Env, SpeechRecord } from '@/types/cloudflare';

/// <reference types="@cloudflare/workers-types" />

// Cloudflare Pages Functions環境での型定義
interface CloudflareRequest extends NextRequest {
  env: Env;
}

export async function GET(request: CloudflareRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q') || '';
    const speaker = searchParams.get('speaker') || '';
    const party = searchParams.get('party') || '';
    const committee = searchParams.get('committee') || '';
    const house = searchParams.get('house') || '';
    const dateFrom = searchParams.get('dateFrom') || '';
    const dateTo = searchParams.get('dateTo') || '';
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');

    // クエリ条件の構築
    const conditions: string[] = [];
    const params: any[] = [];

    if (query) {
      conditions.push('text LIKE ?');
      params.push(`%${query}%`);
    }

    if (speaker) {
      conditions.push('speaker LIKE ?');
      params.push(`%${speaker}%`);
    }

    if (party) {
      conditions.push('party_normalized = ?');
      params.push(party);
    }

    if (committee) {
      conditions.push('committee = ?');
      params.push(committee);
    }

    if (house) {
      conditions.push('house = ?');
      params.push(house);
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
      SELECT * FROM speeches 
      ${whereClause}
      ORDER BY date DESC, id ASC
      LIMIT ? OFFSET ?
    `;

    params.push(limit, offset);

    // D1データベースクエリ実行
    const stmt = request.env.DB.prepare(searchQuery);
    const boundStmt = stmt.bind(...params);
    const result = await boundStmt.all<SpeechRecord>();

    if (!result.success) {
      throw new Error(result.error || 'データベースクエリエラー');
    }

    // 総件数の取得
    const countQuery = `
      SELECT COUNT(*) as total FROM speeches 
      ${whereClause}
    `;
    const countStmt = request.env.DB.prepare(countQuery);
    const boundCountStmt = countStmt.bind(...params.slice(0, -2)); // limit, offsetを除く
    const countResult = await boundCountStmt.first<{ total: number }>();

    const total = countResult?.total || 0;

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
          speaker,
          party,
          committee,
          house,
          dateFrom,
          dateTo
        }
      }
    });

  } catch (error) {
    console.error('検索APIエラー:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '内部サーバーエラー',
        data: []
      },
      { status: 500 }
    );
  }
}

// CORS対応
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