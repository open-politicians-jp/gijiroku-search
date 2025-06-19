/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  distDir: 'out',
  
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
  
  // PWA対応（将来的に）
  // headers: 静的エクスポートでは使用不可
  // セキュリティヘッダーはGitHub Pagesまたはリバースプロキシで設定
}

module.exports = nextConfig