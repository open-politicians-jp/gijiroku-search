/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  distDir: 'out',
  
  // GitHub Pagesの場合、basePath設定が必要な場合がある
  // リポジトリ名がルートでない場合: basePath: '/repository-name'
  basePath: process.env.NODE_ENV === 'production' ? '' : '',
  
  images: {
    unoptimized: true
  },
  
  // GitHub Pages対応
  assetPrefix: process.env.NODE_ENV === 'production' ? '' : '',
  
  experimental: {
    serverComponentsExternalPackages: ['flexsearch']
  },
  
  // 静的ファイル最適化
  compress: true,
  
  // PWA対応（将来的に）
  // headers: 静的エクスポートでは使用不可
  // セキュリティヘッダーはGitHub Pagesまたはリバースプロキシで設定
}

module.exports = nextConfig