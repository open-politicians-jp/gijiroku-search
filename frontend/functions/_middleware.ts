// Cloudflare Pages Functions Middleware
// D1データベースバインディングとCORS設定

/// <reference types="@cloudflare/workers-types" />

export interface CloudflareEnv {
  DB: D1Database;
}

// CORS設定
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
};

// OPTIONSリクエストの処理
export const onRequestOptions: PagesFunction<CloudflareEnv> = async () => {
  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  });
};

// 全リクエストにCORSヘッダーを追加
export const onRequest: PagesFunction<CloudflareEnv> = async (context) => {
  const response = await context.next();
  
  // CORS ヘッダーを追加
  Object.entries(corsHeaders).forEach(([key, value]) => {
    response.headers.set(key, value);
  });

  return response;
};

// 型定義の拡張

export type PagesFunction<Env = unknown> = (
  context: EventContext<Env, any, Record<string, unknown>>
) => Response | Promise<Response>;

export interface EventContext<Env, P, Data> {
  request: Request;
  env: Env;
  params: P;
  data: Data;
  next: (input?: Request | string, init?: RequestInit) => Promise<Response>;
  waitUntil: (promise: Promise<any>) => void;
  passThroughOnException: () => void;
}