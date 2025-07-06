#!/usr/bin/env python3
"""
summary.mdからURL情報を含むpolicy_summaries.jsonを生成するスクリプト
"""

import re
import json
import datetime
from pathlib import Path

def parse_summary_md():
    """summary.mdを解析してJSONデータを生成"""
    
    # ファイルパス
    summary_path = Path("/Users/hironeko/Work/private/new-jp-search/output/summary.md")
    output_path = Path("/Users/hironeko/Work/private/new-jp-search/frontend/public/data/policy_summaries.json")
    
    # ファイル読み込み
    with open(summary_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 政党ごとにセクションを分割
    party_sections = re.split(r'\n## (.+?)\n', content)[1:]  # 最初の空セクションを除外
    
    parties = []
    
    for i in range(0, len(party_sections), 2):
        party_name = party_sections[i]
        party_content = party_sections[i + 1] if i + 1 < len(party_sections) else ""
        
        # 出典URLの解析
        party_references = []
        url_match = re.search(r'\*\*出典\*\*:(.*?)(?=\n###|\n##|$)', party_content, re.DOTALL)
        if url_match:
            url_content = url_match.group(1).strip()
            
            # 単一URLパターン: **出典**: `URL`
            single_url_match = re.match(r'\s*`([^`]+)`', url_content)
            if single_url_match:
                url = single_url_match.group(1)
                party_references.append({
                    "url": url,
                    "description": "公式マニフェスト",
                    "source_type": "official",
                    "reliability": "high"
                })
            else:
                # 複数URLパターン: リスト形式
                urls = re.findall(r'\*\s*`([^`]+)`', url_content)
                for url in urls:
                    party_references.append({
                        "url": url,
                        "description": "公式マニフェスト",
                        "source_type": "official",
                        "reliability": "high"
                    })
                
                # 改行区切りの単一URLパターンも確認
                if not urls:
                    single_urls = re.findall(r'`([^`]+)`', url_content)
                    for url in single_urls:
                        party_references.append({
                            "url": url,
                            "description": "公式マニフェスト",
                            "source_type": "official",
                            "reliability": "high"
                        })
        
        # カテゴリーごとの政策を解析
        categories = []
        category_sections = re.split(r'\n### (.+?)\n', party_content)
        
        # 出典セクションを除去した後のコンテンツから開始
        if url_match:
            # 出典セクション以降から開始
            content_after_source = party_content[url_match.end():]
            category_sections = re.split(r'\n### (.+?)\n', content_after_source)
        
        for j in range(1, len(category_sections), 2):
            category_name = category_sections[j]
            category_content = category_sections[j + 1] if j + 1 < len(category_sections) else ""
            
            # 政策項目を解析
            policies = []
            policy_matches = re.findall(r'\*\s*\*\*(.+?)\*\*:\s*(.+?)(?=\n\*\s*\*\*|\n###|\n##|$)', category_content, re.DOTALL)
            
            for title, description in policy_matches:
                policies.append({
                    "title": title.strip(),
                    "description": description.strip().replace('\n', ' ').replace('  ', ' ')
                })
            
            if policies:  # 政策が存在する場合のみ追加
                categories.append({
                    "category": category_name,
                    "policies": policies
                })
        
        # 政党データを追加
        party_data = {
            "name": party_name,
            "categories": categories
        }
        
        # 政党レベルの参考URLがある場合は追加
        if party_references:
            party_data["party_references"] = party_references
        
        parties.append(party_data)
    
    # JSONデータ構造を作成
    output_data = {
        "generated_at": datetime.datetime.now().isoformat() + "Z",
        "description": "各政党の政策要約 - LLMによる主要政策の分析と要約（URL参照情報付き）",
        "parties": parties,
        "categories": list(set(cat["category"] for party in parties for cat in party["categories"])),
        "total_parties": len(parties),
        "data_source": "summary.md",
        "has_url_references": True
    }
    
    # JSONファイルに出力
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ policy_summaries.json が正常に更新されました")
    print(f"📊 政党数: {len(parties)}")
    print(f"📋 カテゴリ数: {len(output_data['categories'])}")
    
    # URL統計
    total_urls = sum(len(party.get("party_references", [])) for party in parties)
    parties_with_urls = sum(1 for party in parties if party.get("party_references"))
    print(f"🔗 URL参照情報: {total_urls}件 ({parties_with_urls}政党)")

if __name__ == "__main__":
    parse_summary_md()