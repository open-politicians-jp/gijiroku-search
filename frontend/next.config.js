/** @type {import('next').NextConfig} */
const nextConfig = {
  // 静的サイト生成 (GitHub Pages 対応)
  output: 'export',
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  
  // GitHub Pages設定 - ローカル開発時は無効
  basePath: process.env.GITHUB_PAGES === 'true' ? '/gijiroku-search' : '',
  assetPrefix: process.env.GITHUB_PAGES === 'true' ? '/gijiroku-search' : '',
  
  images: {
    unoptimized: true
  },
  
  experimental: {
    serverComponentsExternalPackages: ['flexsearch']
  },
  
  // 静的ファイル最適化
  compress: true,
  
  // 静的エクスポート用の設定
  eslint: {
    ignoreDuringBuilds: false
  },
  typescript: {
    ignoreBuildErrors: false
  }
}

module.exports = nextConfig