#!/usr/bin/env node
/**
 * JSON データファイルからD1データベースへの移行スクリプト
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

class DataMigration {
  constructor() {
    this.dataDir = path.join(__dirname, '../frontend/public/data');
    this.outputDir = path.join(__dirname, '../d1-migration');
    this.ensureOutputDir();
  }

  ensureOutputDir() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * 議事録データの移行SQL生成
   */
  async migrateSpeechesData() {
    console.log('📋 議事録データの移行SQL生成開始...');
    
    const speechFiles = glob.sync(path.join(this.dataDir, 'speeches/**/*.json'));
    const allSpeeches = [];

    for (const file of speechFiles) {
      try {
        const data = JSON.parse(fs.readFileSync(file, 'utf8'));
        if (Array.isArray(data)) {
          allSpeeches.push(...data);
        } else if (data.speeches) {
          allSpeeches.push(...data.speeches);
        }
      } catch (error) {
        console.warn(`⚠️ ${file} の読み込みエラー:`, error.message);
      }
    }

    console.log(`📊 合計 ${allSpeeches.length} 件の議事録データを処理中...`);

    const sqlStatements = allSpeeches.map(speech => {
      const escapedText = this.escapeSql(speech.text || '');
      const escapedSpeaker = this.escapeSql(speech.speaker || '');
      const escapedCommittee = this.escapeSql(speech.committee || '');
      
      return `INSERT OR REPLACE INTO speeches (id, date, session, house, committee, speaker, party, party_normalized, text, url, created_at) VALUES (
        '${speech.id}',
        '${speech.date}',
        ${speech.session || 0},
        '${speech.house || ''}',
        '${escapedCommittee}',
        '${escapedSpeaker}',
        '${speech.party || ''}',
        '${speech.party_normalized || speech.party || ''}',
        '${escapedText}',
        '${speech.url || ''}',
        '${speech.created_at || new Date().toISOString()}'
      );`;
    });

    const sqlContent = [
      '-- 議事録データ移行SQL',
      '-- 生成日時: ' + new Date().toISOString(),
      '',
      'BEGIN TRANSACTION;',
      '',
      ...sqlStatements,
      '',
      'COMMIT;'
    ].join('\n');

    fs.writeFileSync(
      path.join(this.outputDir, 'speeches_migration.sql'),
      sqlContent
    );

    console.log(`✅ 議事録データ移行SQL生成完了: speeches_migration.sql`);
    return allSpeeches.length;
  }

  /**
   * マニフェストデータの移行SQL生成
   */
  async migrateManifestosData() {
    console.log('📋 マニフェストデータの移行SQL生成開始...');
    
    const manifestoFile = path.join(this.dataDir, 'policy_summaries.json');
    
    if (!fs.existsSync(manifestoFile)) {
      console.warn('⚠️ policy_summaries.json が見つかりません');
      return 0;
    }

    const data = JSON.parse(fs.readFileSync(manifestoFile, 'utf8'));
    const parties = data.parties || [];

    console.log(`📊 ${parties.length} 政党のマニフェストデータを処理中...`);

    const sqlStatements = parties.map((party, index) => {
      const id = `manifesto_${index + 1}`;
      const escapedPartyName = this.escapeSql(party.name);
      const escapedBasicTheme = this.escapeSql(party.basic_theme || '');
      
      return `INSERT OR REPLACE INTO manifestos (id, party_name, basic_theme, target_voters, key_policies, categories, party_references, updated_at) VALUES (
        '${id}',
        '${escapedPartyName}',
        '${escapedBasicTheme}',
        '${JSON.stringify(party.target_voters || [])}',
        '${JSON.stringify(party.key_policies || [])}',
        '${JSON.stringify(party.categories || [])}',
        '${JSON.stringify(party.party_references || [])}',
        '${new Date().toISOString()}'
      );`;
    });

    const sqlContent = [
      '-- マニフェストデータ移行SQL',
      '-- 生成日時: ' + new Date().toISOString(),
      '',
      'BEGIN TRANSACTION;',
      '',
      ...sqlStatements,
      '',
      'COMMIT;'
    ].join('\n');

    fs.writeFileSync(
      path.join(this.outputDir, 'manifestos_migration.sql'),
      sqlContent
    );

    console.log(`✅ マニフェストデータ移行SQL生成完了: manifestos_migration.sql`);
    return parties.length;
  }

  /**
   * 質問主意書データの移行SQL生成
   */
  async migrateQuestionsData() {
    console.log('📋 質問主意書データの移行SQL生成開始...');
    
    const questionFiles = glob.sync(path.join(this.dataDir, 'questions/**/*.json'));
    const allQuestions = [];

    for (const file of questionFiles) {
      try {
        const data = JSON.parse(fs.readFileSync(file, 'utf8'));
        if (Array.isArray(data)) {
          allQuestions.push(...data);
        } else if (data.questions) {
          allQuestions.push(...data.questions);
        }
      } catch (error) {
        console.warn(`⚠️ ${file} の読み込みエラー:`, error.message);
      }
    }

    console.log(`📊 合計 ${allQuestions.length} 件の質問主意書データを処理中...`);

    const sqlStatements = allQuestions.map(question => {
      const escapedTitle = this.escapeSql(question.title || '');
      const escapedQuestioner = this.escapeSql(question.questioner || '');
      
      return `INSERT OR REPLACE INTO questions (id, title, questioner, submission_date, status, answer_date, question_url, answer_url, created_at) VALUES (
        '${question.id || question.question_number}',
        '${escapedTitle}',
        '${escapedQuestioner}',
        '${question.submission_date || question.date}',
        '${question.status || '提出済み'}',
        '${question.answer_date || ''}',
        '${question.question_url || question.url}',
        '${question.answer_url || ''}',
        '${question.created_at || new Date().toISOString()}'
      );`;
    });

    const sqlContent = [
      '-- 質問主意書データ移行SQL',
      '-- 生成日時: ' + new Date().toISOString(),
      '',
      'BEGIN TRANSACTION;',
      '',
      ...sqlStatements,
      '',
      'COMMIT;'
    ].join('\n');

    fs.writeFileSync(
      path.join(this.outputDir, 'questions_migration.sql'),
      sqlContent
    );

    console.log(`✅ 質問主意書データ移行SQL生成完了: questions_migration.sql`);
    return allQuestions.length;
  }

  /**
   * SQL文字列のエスケープ
   */
  escapeSql(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/'/g, "''");
  }

  /**
   * 全データ移行の実行
   */
  async migrateAll() {
    console.log('🚀 D1データベース移行開始\n');
    
    const speechCount = await this.migrateSpeechesData();
    const manifestoCount = await this.migrateManifestosData();
    const questionCount = await this.migrateQuestionsData();
    
    // 統合SQLファイルの生成
    const allSqlFiles = [
      'speeches_migration.sql',
      'manifestos_migration.sql',
      'questions_migration.sql'
    ];

    const combinedSql = allSqlFiles
      .map(file => {
        const filePath = path.join(this.outputDir, file);
        return fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : '';
      })
      .filter(content => content.length > 0)
      .join('\n\n');

    fs.writeFileSync(
      path.join(this.outputDir, 'complete_migration.sql'),
      combinedSql
    );

    console.log('\n🎉 データ移行SQL生成完了!');
    console.log(`📊 移行統計:`);
    console.log(`   - 議事録: ${speechCount} 件`);
    console.log(`   - マニフェスト: ${manifestoCount} 件`);
    console.log(`   - 質問主意書: ${questionCount} 件`);
    console.log(`📁 出力ディレクトリ: ${this.outputDir}`);
    
    return {
      speechCount,
      manifestoCount,
      questionCount,
      totalCount: speechCount + manifestoCount + questionCount
    };
  }
}

// スクリプト実行
if (require.main === module) {
  const migration = new DataMigration();
  migration.migrateAll().catch(error => {
    console.error('❌ 移行エラー:', error);
    process.exit(1);
  });
}

module.exports = DataMigration;