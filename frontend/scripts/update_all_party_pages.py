#!/usr/bin/env python3
"""
すべての政党ページにURL参照コンポーネントを追加するスクリプト
"""

import os
import re
from pathlib import Path

def update_party_page(file_path):
    """個別の政党ページファイルを更新"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既に更新済みかチェック
    if 'PolicyReferences' in content:
        print(f"✅ {file_path.name} - 既に更新済み")
        return False
    
    # import文を追加
    import_pattern = r"(import { PolicySummaryData, PartyPolicy } from '@/types/policy';)"
    import_replacement = r"\1\nimport PolicyReferences from '@/components/PolicyReferences';"
    
    if re.search(import_pattern, content):
        content = re.sub(import_pattern, import_replacement, content)
    else:
        print(f"❌ {file_path.name} - import文が見つかりません")
        return False
    
    # 参考資料セクションを追加
    section_pattern = r"(        </div>\n\n        {/\* フッター \*/})"
    section_replacement = """        </div>

        {/* 参考資料・出典 */}
        {partyPolicies.party_references && partyPolicies.party_references.length > 0 && (
          <PolicyReferences 
            references={partyPolicies.party_references}
            className="mb-6"
          />
        )}

        {/* フッター */}"""
    
    if re.search(section_pattern, content):
        content = re.sub(section_pattern, section_replacement, content)
    else:
        print(f"❌ {file_path.name} - フッターセクションが見つかりません")
        return False
    
    # ファイルに書き戻し
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path.name} - 更新完了")
    return True

def main():
    """メイン処理"""
    
    # 政党ページディレクトリ
    party_pages_dir = Path("/Users/hironeko/Work/private/new-jp-search/frontend/app/manifestos/llm")
    
    # すべての政党ページを取得
    party_page_files = list(party_pages_dir.glob("*/page.tsx"))
    
    print(f"🔍 {len(party_page_files)}個の政党ページが見つかりました")
    
    updated_count = 0
    skipped_count = 0
    
    for page_file in party_page_files:
        if update_party_page(page_file):
            updated_count += 1
        else:
            skipped_count += 1
    
    print(f"\n📊 更新結果:")
    print(f"✅ 更新: {updated_count}ページ")
    print(f"⏭️  スキップ: {skipped_count}ページ")
    print(f"📄 合計: {len(party_page_files)}ページ")

if __name__ == "__main__":
    main()