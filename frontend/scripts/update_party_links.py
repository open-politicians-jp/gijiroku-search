#!/usr/bin/env python3
"""
各政党詳細ページのリンクをsummary.mdの出典URLに更新するスクリプト
"""

import re
import os
from pathlib import Path

def update_party_links():
    """政党詳細ページのリンクを動的なURL参照に更新"""
    
    # フロントエンドディレクトリのパス
    frontend_dir = Path("/Users/hironeko/Work/private/new-jp-search/frontend")
    manifestos_dir = frontend_dir / "app" / "manifestos" / "llm"
    
    # 対象のTSXファイルを取得
    tsx_files = list(manifestos_dir.glob("*/page.tsx"))
    
    print(f"📁 {len(tsx_files)}個の政党詳細ページを更新します...")
    
    updated_count = 0
    
    for tsx_file in tsx_files:
        try:
            # ファイル読み込み
            with open(tsx_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 既に更新済みかチェック（より正確に）
            if 'partyPolicies.party_references && partyPolicies.party_references.length > 0' in content:
                print(f"⏭️  {tsx_file.parent.name}: 既に更新済み")
                continue
            
            # "公式サイトを見る"テキストを含むパターンを検索
            if '公式サイトを見る' in content:
                # より広範囲なパターンで置換
                # <div className="flex flex-col sm:flex-row gap-4">から</div>まで
                div_pattern = r'<div className="flex flex-col sm:flex-row gap-4">.*?</div>'
                div_match = re.search(div_pattern, content, re.DOTALL)
                
                if div_match:
                    # 動的リンクコードに置換
                    new_link_section = '''<div className="flex flex-col sm:flex-row gap-4">
            {partyPolicies.party_references && partyPolicies.party_references.length > 0 && (
              <>
                {partyPolicies.party_references.map((ref, index) => (
                  <a
                    key={index}
                    href={ref.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    {ref.description || 'マニフェストを見る'}
                    <ExternalLink className="h-4 w-4 ml-1" />
                  </a>
                ))}
              </>
            )}
            <a
              href="https://www.jimin.jp/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              公式サイト
              <ExternalLink className="h-4 w-4 ml-1" />
            </a>
          </div>'''
                    
                    # 置換実行
                    updated_content = content.replace(div_match.group(0), new_link_section)
                    
                    # ファイル保存
                    with open(tsx_file, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    updated_count += 1
                    print(f"✅ {tsx_file.parent.name}: リンクを動的参照に更新")
                else:
                    print(f"❓ {tsx_file.parent.name}: divパターンが見つかりません")
            else:
                print(f"⏭️  {tsx_file.parent.name}: 更新対象なし")
                
        except Exception as e:
            print(f"❌ {tsx_file.parent.name}: エラー - {e}")
    
    print(f"\n🎉 {updated_count}個のファイルを更新しました")

if __name__ == "__main__":
    update_party_links()