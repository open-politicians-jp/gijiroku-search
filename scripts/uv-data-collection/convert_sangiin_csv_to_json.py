#!/usr/bin/env python3
"""
参議院議員CSVファイルをJSONファイルに変換し、適切なサイズに分割するスクリプト

データソース:
- SmartNews Media Research Institute (SMRI) - House of Councillors Database
- URL: https://smartnews-smri.github.io/house-of-councillors/
- ライセンス: 元ソースのライセンス条項に従う

機能:
- CSVファイルの読み込みと正規化
- 政党名の正規化
- ファイルサイズに基づいた分割 (約50-60名/ファイル)
- frontend/public/data/legislators/ に保存
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class SangiinCSVConverter:
    """参議院議員CSV→JSON変換クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.csv_file = self.project_root / "国会議案データベース.csv"
        self.output_dir = self.project_root / "frontend" / "public" / "data" / "legislators"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 政党名正規化マッピング
        self.party_mapping = {
            '自民': '自由民主党',
            '立憲': '立憲民主党', 
            '維新': '日本維新の会',
            '公明': '公明党',
            '共産': '日本共産党',
            '民主': '国民民主党',
            '沖縄': '沖縄の風',
            'れいわ': 'れいわ新選組',
            '社民': '社会民主党',
            'N国': 'NHK党',
            '無所属': '無所属'
        }
        
    def normalize_party_name(self, party_abbr: str) -> str:
        """政党略称を正式名称に正規化"""
        return self.party_mapping.get(party_abbr, party_abbr)
        
    def extract_birth_year(self, career_text: str) -> Optional[int]:
        """経歴から生年を抽出 (昭和/平成年表記から西暦変換)"""
        try:
            # 昭和XX年パターン
            showa_match = re.search(r'昭和(\d+)年', career_text)
            if showa_match:
                showa_year = int(showa_match.group(1))
                return 1925 + showa_year
                
            # 平成XX年パターン  
            heisei_match = re.search(r'平成(\d+)年', career_text)
            if heisei_match:
                heisei_year = int(heisei_match.group(1))
                return 1988 + heisei_year
                
            # 西暦パターン
            year_match = re.search(r'(\d{4})年', career_text)
            if year_match:
                year = int(year_match.group(1))
                if 1920 <= year <= 2010:  # 妥当な生年範囲
                    return year
                    
        except (ValueError, AttributeError):
            pass
        return None
        
    def parse_election_years(self, election_str: str) -> List[int]:
        """当選年文字列から年のリストを抽出"""
        years = []
        try:
            # "2014、2016、2022" のような形式をパース
            year_parts = re.findall(r'\d{4}', election_str)
            for year_str in year_parts:
                year = int(year_str)
                if 1950 <= year <= 2030:  # 妥当な年範囲
                    years.append(year)
        except (ValueError, AttributeError):
            pass
        return sorted(years)
        
    def extract_constituency_info(self, constituency: str) -> Dict[str, Any]:
        """選挙区情報を分析"""
        if not constituency:
            return {"type": "unknown", "region": None}
            
        if "比例" in constituency:
            return {"type": "proportional", "region": "全国"}
        elif "・" in constituency:
            # "鳥取・島根" のような合区
            return {"type": "combined", "region": constituency}
        else:
            # 単独県
            return {"type": "single", "region": constituency}
    
    def convert_csv_to_json(self) -> List[Dict[str, Any]]:
        """CSVファイルをJSONデータに変換"""
        legislators = []
        
        print(f"📂 CSVファイル読み込み: {self.csv_file}")
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for idx, row in enumerate(reader, 1):
                try:
                    # 基本情報の抽出
                    name = row.get('議員氏名', '').strip()
                    if not name:
                        continue
                        
                    # 政党名正規化
                    party_abbr = row.get('会派', '').strip()
                    party_normalized = self.normalize_party_name(party_abbr)
                    
                    # 選挙区情報の分析
                    constituency_str = row.get('選挙区', '').strip()
                    constituency_info = self.extract_constituency_info(constituency_str)
                    
                    # 当選年の解析
                    election_str = row.get('当選年', '').strip()
                    election_years = self.parse_election_years(election_str)
                    first_election_year = election_years[0] if election_years else None
                    
                    # 当選回数
                    term_count_str = row.get('当選回数', '').strip()
                    try:
                        term_count = int(term_count_str) if term_count_str.isdigit() else len(election_years)
                    except ValueError:
                        term_count = len(election_years)
                    
                    # 生年の抽出
                    career_text = row.get('経歴', '')
                    birth_year = self.extract_birth_year(career_text)
                    
                    # 任期満了日
                    term_end = row.get('任期満了', '').strip()
                    
                    # 役職情報
                    positions = row.get('役職等', '').strip()
                    
                    # 議員データの構築
                    legislator = {
                        "id": f"sangiin_{idx:03d}",
                        "name": name,
                        "house": "sangiin",
                        "party": party_normalized,
                        "party_original": party_abbr,
                        "constituency": constituency_str,
                        "constituency_type": constituency_info["type"],
                        "region": constituency_info["region"],
                        "election_years": election_years,
                        "first_election_year": first_election_year,
                        "term_count": term_count,
                        "term_end": term_end,
                        "status": "active",  # 現職データと仮定
                        "birth_year": birth_year,
                        "positions": positions,
                        "profile_url": row.get('議員個人の紹介ページ', '').strip(),
                        "photo_url": row.get('写真URL', '').strip(),
                        "reading": row.get('読み方', '').strip(),
                        "real_name": row.get('通称名使用議員の本名', '').strip(),
                        "career": career_text.strip(),
                        "career_updated": row.get('経歴の時点', '').strip()
                    }
                    
                    legislators.append(legislator)
                    
                except Exception as e:
                    print(f"⚠️ 行{idx}の処理でエラー: {e}")
                    continue
                    
        print(f"✅ {len(legislators)}名の議員データを変換完了")
        return legislators
        
    def split_and_save(self, legislators: List[Dict[str, Any]], legislators_per_file: int = 60):
        """議員データを分割してJSONファイルに保存"""
        total_legislators = len(legislators)
        file_count = (total_legislators + legislators_per_file - 1) // legislators_per_file
        
        print(f"📁 {total_legislators}名を{legislators_per_file}名/ファイルで{file_count}ファイルに分割")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i in range(file_count):
            start_idx = i * legislators_per_file
            end_idx = min(start_idx + legislators_per_file, total_legislators)
            
            chunk_legislators = legislators[start_idx:end_idx]
            
            # ファイル名: sangiin_legislators_YYYYMMDD_HHMMSS_part1.json
            filename = f"sangiin_legislators_{timestamp}_part{i+1:02d}.json"
            filepath = self.output_dir / filename
            
            # メタデータ付きでJSONファイル作成
            json_data = {
                "metadata": {
                    "house": "sangiin",
                    "data_type": "legislators",
                    "total_count": len(chunk_legislators),
                    "part_number": i + 1,
                    "total_parts": file_count,
                    "legislators_range": f"{start_idx + 1}-{end_idx}",
                    "generated_at": datetime.now().isoformat(),
                    "source_file": "国会議案データベース.csv",
                    "source_url": "https://smartnews-smri.github.io/house-of-councillors/",
                    "source_attribution": "SmartNews Media Research Institute (SMRI) - House of Councillors Database",
                    "data_quality": "official_sangiin_data",
                    "license": "Please refer to the original source for license information"
                },
                "data": chunk_legislators
            }
            
            # JSONファイル保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
                
            file_size = filepath.stat().st_size / (1024 * 1024)
            print(f"💾 {filename}: {len(chunk_legislators)}名 ({file_size:.1f} MB)")
            
        # 統合ファイルも作成
        unified_filename = f"sangiin_legislators_unified_{timestamp}.json"
        unified_filepath = self.output_dir / unified_filename
        
        unified_data = {
            "metadata": {
                "house": "sangiin", 
                "data_type": "legislators_unified",
                "total_count": total_legislators,
                "total_parts": file_count,
                "generated_at": datetime.now().isoformat(),
                "source_file": "国会議案データベース.csv",
                "source_url": "https://smartnews-smri.github.io/house-of-councillors/",
                "source_attribution": "SmartNews Media Research Institute (SMRI) - House of Councillors Database",
                "data_quality": "official_sangiin_data",
                "license": "Please refer to the original source for license information"
            },
            "data": legislators
        }
        
        with open(unified_filepath, 'w', encoding='utf-8') as f:
            json.dump(unified_data, f, ensure_ascii=False, indent=2)
            
        unified_size = unified_filepath.stat().st_size / (1024 * 1024)
        print(f"📚 統合ファイル: {unified_filename} ({unified_size:.1f} MB)")
        
    def generate_summary_stats(self, legislators: List[Dict[str, Any]]):
        """議員データの統計サマリーを生成"""
        print("\n📊 参議院議員データ統計:")
        print(f"総議員数: {len(legislators)}名")
        
        # 政党別集計
        party_counts = {}
        for leg in legislators:
            party = leg['party']
            party_counts[party] = party_counts.get(party, 0) + 1
            
        print("\n🏛️ 政党別議員数:")
        for party, count in sorted(party_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {party}: {count}名")
            
        # 選挙区タイプ別集計
        constituency_types = {}
        for leg in legislators:
            const_type = leg['constituency_type']
            constituency_types[const_type] = constituency_types.get(const_type, 0) + 1
            
        print("\n🗳️ 選挙区タイプ別:")
        for const_type, count in constituency_types.items():
            print(f"  {const_type}: {count}名")

def main():
    """メイン処理"""
    print("🚀 参議院議員CSV→JSON変換開始")
    
    converter = SangiinCSVConverter()
    
    # CSV存在確認
    if not converter.csv_file.exists():
        print(f"❌ CSVファイルが見つかりません: {converter.csv_file}")
        return
        
    # CSV→JSON変換
    legislators = converter.convert_csv_to_json()
    
    if not legislators:
        print("❌ 議員データが取得できませんでした")
        return
        
    # 統計表示
    converter.generate_summary_stats(legislators)
    
    # 分割保存
    converter.split_and_save(legislators)
    
    print("\n✨ 参議院議員JSON変換完了!")

if __name__ == "__main__":
    main()