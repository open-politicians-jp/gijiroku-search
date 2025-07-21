import { NextRequest, NextResponse } from 'next/server';
import { Env, QuestionRecord } from '@/types/cloudflare';

/// <reference types="@cloudflare/workers-types" />
interface CloudflareRequest extends NextRequest {
  env: Env;
}

export async function GET(request: CloudflareRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q') || '';
    const questioner = searchParams.get('questioner') || '';
    const status = searchParams.get('status') || '';
    const dateFrom = searchParams.get('dateFrom') || '';
    const dateTo = searchParams.get('dateTo') || '';
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    // クエリ条件の構築
    const conditions: string[] = [];
    const params: any[] = [];

    if (query) {
      conditions.push('title LIKE ?');
      params.push(`%${query}%`);
    }

    if (questioner) {
      conditions.push('questioner LIKE ?');
      params.push(`%${questioner}%`);
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
      SELECT * FROM questions 
      ${whereClause}
      ORDER BY submission_date DESC, id ASC
      LIMIT ? OFFSET ?
    `;

    params.push(limit, offset);

    // D1データベースクエリ実行
    const result = await request.env.DB.prepare(searchQuery).bind(...params).all<QuestionRecord>();

    if (!result.success) {
      throw new Error(result.error || 'データベースクエリエラー');
    }

    // 総件数の取得
    const countQuery = `
      SELECT COUNT(*) as total FROM questions 
      ${whereClause}
    `;
    const countParams = params.slice(0, -2); // limit, offsetを除く
    const countResult = await request.env.DB.prepare(countQuery).bind(...countParams).first<{ total: number }>();

    const total = countResult?.total || 0;

    // ステータス別統計
    const statusStatsQuery = `
      SELECT 
        status,
        COUNT(*) as count
      FROM questions
      GROUP BY status
      ORDER BY count DESC
    `;
    const statusStats = await request.env.DB.prepare(statusStatsQuery).all();

    // 質問者別統計（上位20名）
    const questionerStatsQuery = `
      SELECT 
        questioner,
        COUNT(*) as question_count,
        COUNT(CASE WHEN answer_date IS NOT NULL THEN 1 END) as answered_count
      FROM questions
      WHERE questioner != ''
      GROUP BY questioner
      ORDER BY question_count DESC
      LIMIT 20
    `;
    const questionerStats = await request.env.DB.prepare(questionerStatsQuery).all();

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
          questioner,
          status,
          dateFrom,
          dateTo
        },
        stats: {
          status: statusStats.results,
          top_questioners: questionerStats.results
        }
      }
    });

  } catch (error) {
    console.error('質問主意書APIエラー:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '質問主意書データの取得に失敗しました',
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