import { NextRequest, NextResponse } from 'next/server';
import { Env, ManifestoRecord } from '@/types/cloudflare';

/// <reference types="@cloudflare/workers-types" />
interface CloudflareRequest extends NextRequest {
  env: Env;
}

export async function GET(request: CloudflareRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const party = searchParams.get('party');
    const format = searchParams.get('format') || 'structured';

    let query: string;
    let params: any[] = [];

    if (party) {
      // 特定政党のマニフェスト取得
      query = 'SELECT * FROM manifestos WHERE party_name = ?';
      params = [party];
    } else {
      // 全政党のマニフェスト取得
      query = 'SELECT * FROM manifestos ORDER BY party_name';
    }

    const result = await request.env.DB.prepare(query).bind(...params).all<ManifestoRecord>();

    if (!result.success) {
      throw new Error(result.error || 'データベースクエリエラー');
    }

    // JSONフィールドをパース
    const processedData = result.results.map(manifesto => {
      try {
        return {
          ...manifesto,
          target_voters: manifesto.target_voters ? JSON.parse(manifesto.target_voters) : [],
          key_policies: manifesto.key_policies ? JSON.parse(manifesto.key_policies) : [],
          categories: manifesto.categories ? JSON.parse(manifesto.categories) : [],
          party_references: manifesto.party_references ? JSON.parse(manifesto.party_references) : []
        };
      } catch (parseError) {
        console.warn(`マニフェストJSONパースエラー (${manifesto.party_name}):`, parseError);
        return {
          ...manifesto,
          target_voters: [],
          key_policies: [],
          categories: [],
          party_references: []
        };
      }
    });

    // レスポンス形式の選択
    if (format === 'simple') {
      // シンプル形式（政党名とbasic_themeのみ）
      const simpleData = processedData.map(manifesto => ({
        party_name: manifesto.party_name,
        basic_theme: manifesto.basic_theme,
        updated_at: manifesto.updated_at
      }));

      return NextResponse.json({
        success: true,
        data: simpleData,
        meta: {
          total: simpleData.length,
          format: 'simple'
        }
      });
    }

    // 構造化形式（完全なデータ）
    if (party && processedData.length === 1) {
      // 単一政党の詳細
      return NextResponse.json({
        success: true,
        data: processedData[0],
        meta: {
          party_name: party,
          format: 'detailed'
        }
      });
    }

    // 全政党または複数政党
    return NextResponse.json({
      success: true,
      data: processedData,
      meta: {
        total: processedData.length,
        format: 'structured',
        available_parties: processedData.map(m => m.party_name)
      }
    });

  } catch (error) {
    console.error('マニフェストAPIエラー:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'マニフェストデータの取得に失敗しました',
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