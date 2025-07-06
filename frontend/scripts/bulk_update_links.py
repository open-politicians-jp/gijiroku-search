#!/usr/bin/env python3
"""
政党詳細ページのリンクを一括更新
"""

import os
from pathlib import Path

# 更新が必要なファイルのリスト（自由民主党と立憲民主党は既に更新済み）
files_to_update = [
    "nipponishin", "genzei-nihon", "kakuyugo-to", "kokka-seishin-kai", 
    "komeito", "kokuminminshuto", "nihon-katei-mamoru-kai", "kokusei-governance",
    "shinto-kunimori", "reiwa", "saisei-no-michi", "kyosanto", "nhk-to",
    "sanseito", "shakai-minshu-to", "nihon-kaikaku-to", "shinto-yamato",
    "zeikin-tomei-ka-to", "nihon-hoshu-to"
]

def update_single_file(file_dir):
    """単一ファイルのリンクを更新"""
    file_path = Path(f"/Users/hironeko/Work/private/new-jp-search/frontend/app/manifestos/llm/{file_dir}/page.tsx")
    
    if not file_path.exists():
        print(f"❌ {file_dir}: ファイルが見つかりません")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 既に更新済みかチェック
        if 'partyPolicies.party_references && partyPolicies.party_references.length > 0' in content:
            print(f"⏭️  {file_dir}: 既に更新済み")
            return False
        
        # "公式サイトを見る" を含む行から </div> まで置換
        lines = content.split('\n')
        updated_lines = []
        in_link_section = False
        link_section_start = -1
        
        for i, line in enumerate(lines):
            if '公式サイトを見る' in line and 'href=' in lines[i-5:i+1]:
                # リンクセクションの開始を見つける
                for j in range(i-10, i):
                    if j >= 0 and 'flex flex-col sm:flex-row gap-4' in lines[j]:
                        link_section_start = j
                        break
                
                if link_section_start >= 0:
                    # 新しいリンクセクションを挿入
                    new_section = [
                        '          <div className="flex flex-col sm:flex-row gap-4">',
                        '            {partyPolicies.party_references && partyPolicies.party_references.length > 0 && (',
                        '              <>',
                        '                {partyPolicies.party_references.map((ref, index) => (',
                        '                  <a',
                        '                    key={index}',
                        '                    href={ref.url}',
                        '                    target="_blank"',
                        '                    rel="noopener noreferrer"',
                        '                    className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"',
                        '                  >',
                        '                    {ref.description || \'マニフェストを見る\'}',
                        '                    <ExternalLink className="h-4 w-4 ml-1" />',
                        '                  </a>',
                        '                ))}',
                        '              </>',
                        '            )}',
                        '            <a',
                        '              href="https://www.jimin.jp/"',
                        '              target="_blank"',
                        '              rel="noopener noreferrer"',
                        '              className="inline-flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"',
                        '            >',
                        '              公式サイト',
                        '              <ExternalLink className="h-4 w-4 ml-1" />',
                        '            </a>',
                        '          </div>'
                    ]
                    
                    # 古いセクションをスキップして新しいセクションに置換
                    updated_lines = lines[:link_section_start] + new_section
                    
                    # </div> まで飛ばす
                    for k in range(i+1, len(lines)):
                        if '</div>' in lines[k] and '          </div>' == lines[k]:
                            updated_lines.extend(lines[k+1:])
                            break
                    break
        
        if updated_lines:
            # ファイルを更新
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(updated_lines))
            print(f"✅ {file_dir}: リンクを動的参照に更新")
            return True
        else:
            print(f"❓ {file_dir}: 更新対象が見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ {file_dir}: エラー - {e}")
        return False

def main():
    print(f"📁 {len(files_to_update)}個のファイルを更新します...")
    
    updated_count = 0
    for file_dir in files_to_update:
        if update_single_file(file_dir):
            updated_count += 1
    
    print(f"\n🎉 {updated_count}個のファイルを更新しました")

if __name__ == "__main__":
    main()