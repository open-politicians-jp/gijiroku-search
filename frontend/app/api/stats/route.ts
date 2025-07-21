import { NextRequest, NextResponse } from 'next/server';
import { Env } from '@/types/cloudflare';

/// <reference types="@cloudflare/workers-types" />

interface CloudflareRequest extends NextRequest {
  env: Env;
}

export async function GET(request: CloudflareRequest) {
  try {
    // 基本統計の取得
    const statsQuery = `
      SELECT 
        COUNT(*) as total_speeches,
        COUNT(DISTINCT speaker) as total_speakers,
        COUNT(DISTINCT party_normalized) as total_parties,
        COUNT(DISTINCT committee) as total_committees,
        COUNT(DISTINCT session) as total_sessions,
        MIN(date) as earliest_date,
        MAX(date) as latest_date
      FROM speeches
    `;

    const statsResult = await request.env.DB.prepare(statsQuery).first();

    // 政党別統計
    const partyStatsQuery = `
      SELECT 
        party_normalized as party,
        COUNT(*) as speech_count,
        COUNT(DISTINCT speaker) as speaker_count
      FROM speeches
      WHERE party_normalized != ''
      GROUP BY party_normalized
      ORDER BY speech_count DESC
    `;

    const partyStats = await request.env.DB.prepare(partyStatsQuery).all();

    // 発言者別統計（上位50名）
    const speakerStatsQuery = `
      SELECT 
        speaker,
        party_normalized as party,
        COUNT(*) as speech_count
      FROM speeches
      WHERE speaker != ''
      GROUP BY speaker, party_normalized
      ORDER BY speech_count DESC
      LIMIT 50
    `;

    const speakerStats = await request.env.DB.prepare(speakerStatsQuery).all();

    // 委員会別統計
    const committeeStatsQuery = `
      SELECT 
        committee,
        COUNT(*) as speech_count,
        COUNT(DISTINCT speaker) as speaker_count,
        COUNT(DISTINCT party_normalized) as party_count
      FROM speeches
      WHERE committee != ''
      GROUP BY committee
      ORDER BY speech_count DESC
    `;

    const committeeStats = await request.env.DB.prepare(committeeStatsQuery).all();

    // セッション別統計
    const sessionStatsQuery = `
      SELECT 
        session,
        house,
        COUNT(*) as speech_count,
        COUNT(DISTINCT speaker) as speaker_count,
        MIN(date) as start_date,
        MAX(date) as end_date
      FROM speeches
      WHERE session > 0
      GROUP BY session, house
      ORDER BY session DESC, house
    `;

    const sessionStats = await request.env.DB.prepare(sessionStatsQuery).all();

    // 月別統計（過去12ヶ月）
    const monthlyStatsQuery = `
      SELECT 
        substr(date, 1, 7) as month,
        COUNT(*) as speech_count,
        COUNT(DISTINCT speaker) as speaker_count
      FROM speeches
      WHERE date >= date('now', '-12 months')
      GROUP BY substr(date, 1, 7)
      ORDER BY month DESC
    `;

    const monthlyStats = await request.env.DB.prepare(monthlyStatsQuery).all();

    return NextResponse.json({
      success: true,
      data: {
        overview: statsResult,
        parties: partyStats.results,
        speakers: speakerStats.results,
        committees: committeeStats.results,
        sessions: sessionStats.results,
        monthly: monthlyStats.results
      },
      meta: {
        generated_at: new Date().toISOString(),
        cache_duration: 3600 // 1時間キャッシュ推奨
      }
    });

  } catch (error) {
    console.error('統計APIエラー:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '統計データの取得に失敗しました',
        data: null
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