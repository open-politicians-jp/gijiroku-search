/**
 * 検索機能テスト用モジュール
 */

import { dataLoader } from './data-loader';

export async function testSearch() {
  console.log('=== 検索機能テスト開始 ===');
  
  try {
    // 1. 議事録データ読み込みテスト
    console.log('1. 議事録データ読み込み中...');
    const speeches = await dataLoader.loadSpeeches();
    console.log(`議事録データ件数: ${speeches.length}`);
    
    if (speeches.length > 0) {
      console.log('サンプル議事録:', speeches[0]);
    }
    
    // 2. 委員会ニュースデータ読み込みテスト
    console.log('2. 委員会ニュースデータ読み込み中...');
    const news = await dataLoader.loadCommitteeNews();
    console.log(`委員会ニュース件数: ${news.length}`);
    
    if (news.length > 0) {
      console.log('サンプル委員会ニュース:', news[0]);
    }
    
    // 3. 統計データテスト
    console.log('3. 統計データ計算中...');
    const stats = await dataLoader.loadStats();
    console.log('統計データ:', {
      total_speeches: stats.total_speeches,
      top_parties_count: stats.top_parties.length,
      top_speakers_count: stats.top_speakers.length,
      date_range: stats.date_range
    });
    
    // 4. 検索テスト
    console.log('4. 検索テスト実行中...');
    
    // 議事録検索テスト
    const searchResult = await dataLoader.searchSpeeches({
      q: '政策',
      limit: 5
    });
    console.log(`政策検索結果: ${searchResult.total}件中${searchResult.speeches.length}件表示`);
    
    // 委員会ニュース検索テスト
    const committeeSearchResult = await dataLoader.searchCommitteeNews({
      q: '内閣委員会',
      limit: 5
    });
    console.log(`内閣委員会検索結果: ${committeeSearchResult.total}件中${committeeSearchResult.news.length}件表示`);
    
    console.log('=== 検索機能テスト完了 ===');
    return true;
    
  } catch (error) {
    console.error('検索機能テストエラー:', error);
    return false;
  }
}

// ブラウザ環境でのテスト実行
if (typeof window !== 'undefined') {
  (window as any).testSearch = testSearch;
}