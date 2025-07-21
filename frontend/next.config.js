/** @type {import('next').NextConfig} */
const nextConfig = {
  // Cloudflare Pages対応設定
  // output: 'export', // ← 削除（動的機能を使用するため）
  
  // 画像最適化無効（Cloudflare Pages対応）
  images: {
    unoptimized: true
  },
  
  // サーバーコンポーネント外部パッケージ
  experimental: {
    serverComponentsExternalPackages: ['flexsearch']
  },
  
  // 圧縮有効化
  compress: true,
  
  // ビルド設定
  eslint: {
    ignoreDuringBuilds: false
  },
  typescript: {
    ignoreBuildErrors: false
  },
  
  // Cloudflare Pages Functions対応
  webpack: (config) => {
    // D1バインディング用の設定
    config.externals = [...(config.externals || []), '@cloudflare/workers-types'];
    return config;
  }
}

module.exports = nextConfig