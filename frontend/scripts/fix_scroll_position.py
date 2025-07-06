#!/usr/bin/env python3
"""
すべての政党ページにスクロールリセット機能を追加するスクリプト
"""

import os
import re
from pathlib import Path

def fix_scroll_position(file_path):
    """個別の政党ページファイルにスクロールリセットを追加"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既に修正済みかチェック
    if 'window.scrollTo(0, 0);' in content:
        print(f"✅ {file_path.name} - 既に修正済み")
        return False
    
    # useEffectの先頭にスクロールリセットを追加
    pattern = r"(  useEffect\(\(\) => \{\s*\n)(    const loadPartyDetail)"
    replacement = r"\1    // ページ読み込み時にトップにスクロール\n    window.scrollTo(0, 0);\n    \n\2"
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
    else:
        print(f"❌ {file_path.name} - useEffectパターンが見つかりません")
        return False
    
    # ファイルに書き戻し
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path.name} - スクロールリセット追加完了")
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
        if fix_scroll_position(page_file):
            updated_count += 1
        else:
            skipped_count += 1
    
    print(f"\n📊 スクロールリセット修正結果:")
    print(f"✅ 更新: {updated_count}ページ")
    print(f"⏭️  スキップ: {skipped_count}ページ")
    print(f"📄 合計: {len(party_page_files)}ページ")

if __name__ == "__main__":
    main()