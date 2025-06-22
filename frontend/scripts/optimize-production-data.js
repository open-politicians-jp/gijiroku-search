#!/usr/bin/env node

/**
 * Production data optimization for GitHub Pages deployment
 * 
 * このスクリプトは、GitHub Pagesのファイルサイズ制限に対応するため、
 * 本番環境向けに最適化されたデータセットを生成します。
 */

const fs = require('fs');
const path = require('path');

const PUBLIC_DATA_DIR = path.join(__dirname, '../public/data');
const SPEECHES_DIR = path.join(PUBLIC_DATA_DIR, 'speeches');

// GitHub Pages制限: 各ファイル100MB以下、リポジトリ全体1GB以下推奨
const MAX_FILE_SIZE_MB = 50; // 安全マージンを考慮して50MBに設定
const MAX_SPEECHES_PER_CHUNK = 2500; // チャンクあたりの発言数を削減

/**
 * ファイルサイズをMBで取得
 */
function getFileSizeMB(filePath) {
  if (!fs.existsSync(filePath)) return 0;
  const stats = fs.statSync(filePath);
  return (stats.size / (1024 * 1024)).toFixed(2);
}

/**
 * 大容量チャンクファイルを最適化
 */
async function optimizeChunkFiles() {
  console.log('🔧 Starting production data optimization...');
  
  try {
    // インデックスファイルを読み込み
    const indexPath = path.join(SPEECHES_DIR, 'speeches_index.json');
    if (!fs.existsSync(indexPath)) {
      console.error('❌ speeches_index.json not found');
      return false;
    }

    const indexData = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
    console.log(`📊 Original total speeches: ${indexData.metadata.total_count}`);

    const optimizedChunks = [];
    let totalOptimizedSpeeches = 0;

    // 各チャンクファイルを処理
    for (let i = 1; i <= indexData.metadata.total_chunks; i++) {
      const chunkFileName = `speeches_chunk_${i.toString().padStart(2, '0')}.json`;
      const chunkPath = path.join(SPEECHES_DIR, chunkFileName);
      
      if (!fs.existsSync(chunkPath)) {
        console.warn(`⚠️ Chunk file not found: ${chunkFileName}`);
        continue;
      }

      const fileSizeMB = getFileSizeMB(chunkPath);
      console.log(`📁 Processing ${chunkFileName} (${fileSizeMB}MB)`);

      if (fileSizeMB > MAX_FILE_SIZE_MB) {
        // 大容量ファイルを最適化
        const chunkData = JSON.parse(fs.readFileSync(chunkPath, 'utf8'));
        const originalCount = chunkData.data.length;

        // 最新のデータを優先して取得
        const optimizedData = chunkData.data
          .sort((a, b) => b.date.localeCompare(a.date))
          .slice(0, MAX_SPEECHES_PER_CHUNK);

        // 最適化されたファイルを保存
        const optimizedChunk = {
          ...chunkData,
          data: optimizedData,
          metadata: {
            ...chunkData.metadata,
            original_count: originalCount,
            optimized_count: optimizedData.length,
            optimization_note: 'Optimized for GitHub Pages deployment'
          }
        };

        fs.writeFileSync(chunkPath, JSON.stringify(optimizedChunk, null, 2));
        
        const newSizeMB = getFileSizeMB(chunkPath);
        console.log(`✅ Optimized ${chunkFileName}: ${originalCount} → ${optimizedData.length} speeches (${fileSizeMB}MB → ${newSizeMB}MB)`);
        
        optimizedChunks.push({
          chunk_number: i,
          filename: chunkFileName,
          count: optimizedData.length,
          date_range: {
            from: optimizedData[optimizedData.length - 1]?.date || '',
            to: optimizedData[0]?.date || ''
          }
        });

        totalOptimizedSpeeches += optimizedData.length;
      } else {
        // サイズが適切なファイルはそのまま
        const chunkData = JSON.parse(fs.readFileSync(chunkPath, 'utf8'));
        optimizedChunks.push({
          chunk_number: i,
          filename: chunkFileName,
          count: chunkData.data.length,
          date_range: {
            from: chunkData.data[chunkData.data.length - 1]?.date || '',
            to: chunkData.data[0]?.date || ''
          }
        });
        
        totalOptimizedSpeeches += chunkData.data.length;
        console.log(`✅ Keeping ${chunkFileName}: ${chunkData.data.length} speeches (${fileSizeMB}MB)`);
      }
    }

    // 最適化されたインデックスファイルを生成
    const optimizedIndex = {
      metadata: {
        ...indexData.metadata,
        total_count: totalOptimizedSpeeches,
        total_chunks: optimizedChunks.length,
        optimization_applied: true,
        optimization_date: new Date().toISOString()
      },
      chunks: optimizedChunks
    };

    fs.writeFileSync(indexPath, JSON.stringify(optimizedIndex, null, 2));
    
    console.log('🎉 Production optimization completed!');
    console.log(`📊 Total speeches: ${indexData.metadata.total_count} → ${totalOptimizedSpeeches}`);
    console.log(`📁 Total chunks: ${indexData.metadata.total_chunks} → ${optimizedChunks.length}`);
    
    return true;

  } catch (error) {
    console.error('❌ Error during optimization:', error);
    return false;
  }
}

/**
 * 最適化後のファイルサイズ確認
 */
function checkOptimizedSizes() {
  console.log('\n📊 Checking optimized file sizes...');
  
  const chunkFiles = fs.readdirSync(SPEECHES_DIR)
    .filter(file => file.startsWith('speeches_chunk_') && file.endsWith('.json'))
    .sort();

  let totalSizeMB = 0;
  
  chunkFiles.forEach(file => {
    const filePath = path.join(SPEECHES_DIR, file);
    const sizeMB = getFileSizeMB(filePath);
    totalSizeMB += parseFloat(sizeMB);
    
    const status = parseFloat(sizeMB) > MAX_FILE_SIZE_MB ? '⚠️' : '✅';
    console.log(`${status} ${file}: ${sizeMB}MB`);
  });

  console.log(`\n📈 Total speeches data size: ${totalSizeMB.toFixed(2)}MB`);
  
  if (totalSizeMB > 500) {
    console.warn('⚠️ Warning: Total size exceeds 500MB - consider further optimization');
  } else {
    console.log('✅ Total size is within acceptable limits for GitHub Pages');
  }
}

// メイン実行
async function main() {
  if (process.env.GITHUB_PAGES === 'true') {
    console.log('🌐 GitHub Pages deployment detected - optimizing data...');
    
    const success = await optimizeChunkFiles();
    if (success) {
      checkOptimizedSizes();
    } else {
      console.error('❌ Optimization failed');
      process.exit(1);
    }
  } else {
    console.log('🏠 Local environment - skipping optimization');
  }
}

// CLI実行時
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { optimizeChunkFiles, checkOptimizedSizes };