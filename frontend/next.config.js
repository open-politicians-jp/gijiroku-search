/** @type {import('next').NextConfig} */
const nextConfig = {
  // 静的サイト生成を基本とし、環境変数でAPI routesを有効化
  output: process.env.NEXT_PUBLIC_USE_API_ROUTES === 'true' ? 'standalone' : 'export',
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  distDir: 'out',
  
  // GitHub Pages設定 - ローカル開発時は無効
  basePath: process.env.GITHUB_PAGES === 'true' || process.env.NODE_ENV === 'production' ? '/gijiroku-search' : '',
  assetPrefix: process.env.GITHUB_PAGES === 'true' || process.env.NODE_ENV === 'production' ? '/gijiroku-search/' : '',
  
  images: {
    unoptimized: true
  },
  
  experimental: {
    serverComponentsExternalPackages: ['flexsearch']
  },
  
  // 静的ファイル最適化
  compress: true,
  
  // バージョン情報の設定
  publicRuntimeConfig: {
    version: process.env.NEXT_PUBLIC_VERSION || require('./package.json').version,
    buildTime: process.env.NEXT_PUBLIC_BUILD_TIME || new Date().toISOString(),
    gitCommit: process.env.GITHUB_SHA || 'local',
  },
  
  // Webpack設定の最適化
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
  
  // PWA対応（将来的に）
  // headers: 静的エクスポートでは使用不可
  // セキュリティヘッダーはGitHub Pagesまたはリバースプロキシで設定
}

module.exports = nextConfig