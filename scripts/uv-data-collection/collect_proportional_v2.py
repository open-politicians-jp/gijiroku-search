#!/usr/bin/env python3
"""
比例代表データ収集 v2 - クライアントサイドレンダリング対応
"""

import json
import logging
import re
import requests
from datetime import datetime
from pathlib import Path
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_proportional_v2():
    """比例代表データ収集 v2 - よりターゲット化された手法"""
    logger.info("🚀 比例代表データ収集 v2 開始...")
    
    collector = Go2senkyoOptimizedCollector()
    all_proportional_candidates = []
    
    # 実際に利用可能な政党IDを取得
    proportional_parties = get_available_parties(collector)
    
    if not proportional_parties:
        logger.warning("利用可能な政党が見つかりません")
        return []
    
    try:
        # 各政党の比例代表候補者を収集
        for party_info in proportional_parties:
            try:
                party_name = party_info['name']
                party_id = party_info['id']
                
                logger.info(f"📍 {party_name} (ID:{party_id}) 比例代表収集中...")
                
                # 政党別ページからデータを取得
                url = f"{collector.base_url}/2025/hirei/{party_id}"
                collector.random_delay(1, 2)
                
                response = collector.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"{party_name}: HTTP {response.status_code}")
                    continue
                
                # HTMLからJavaScriptのデータ部分を抽出
                candidates = extract_candidates_from_html(response.text, party_name, url, collector)
                
                if candidates:
                    all_proportional_candidates.extend(candidates)
                    logger.info(f"✅ {party_name}: {len(candidates)}名")
                    
                    # サンプル表示
                    if candidates:
                        sample = candidates[0]
                        logger.info(f"  サンプル: {sample.get('name', 'N/A')} ({sample.get('party', 'N/A')})")
                else:
                    logger.warning(f"{party_name}: 候補者データが見つかりません")
                
            except Exception as e:
                logger.error(f"❌ {party_name}エラー: {e}")
                continue
        
        logger.info(f"🎯 比例代表収集完了: {len(all_proportional_candidates)}名")
        return all_proportional_candidates
        
    except Exception as e:
        logger.error(f"❌ 比例代表収集エラー: {e}") 
        raise

def get_available_parties(collector):
    """利用可能な政党一覧を取得"""
    logger.info("🔍 利用可能な政党一覧を取得中...")
    
    try:
        # メインページから政党情報を取得
        url = f"{collector.base_url}/2025"
        response = collector.session.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"メインページアクセス失敗: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 比例代表政党リンクを探す
        parties = []
        hirei_links = soup.find_all('a', href=re.compile(r'/2025/hirei/\d+'))
        
        for link in hirei_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # IDを抽出
            match = re.search(r'/hirei/(\d+)', href)
            if match and text:
                party_id = match.group(1)
                parties.append({
                    'name': text,
                    'id': party_id,
                    'url': href
                })
        
        # 重複を削除
        unique_parties = []
        seen_ids = set()
        for party in parties:
            if party['id'] not in seen_ids:
                unique_parties.append(party)
                seen_ids.add(party['id'])
        
        logger.info(f"📋 発見された政党: {len(unique_parties)}個")
        for party in unique_parties[:10]:  # 最初の10個を表示
            logger.info(f"  - {party['name']} (ID: {party['id']})")
        
        return unique_parties
        
    except Exception as e:
        logger.error(f"政党一覧取得エラー: {e}")
        return []

def extract_candidates_from_html(html_content, party_name, page_url, collector):
    """HTMLコンテンツから候補者情報を抽出"""
    candidates = []
    
    try:
        # まず通常のHTML解析を試す
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Next.jsのサーバーサイドレンダリングデータを探す
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'hireiList' in script.string:
                # JSON データを探す
                json_matches = re.findall(r'\{[^{}]*"hireiList"[^{}]*\}', script.string)
                for match in json_matches:
                    try:
                        # JSON を安全に解析
                        data = json.loads(match)
                        if 'hireiList' in data:
                            logger.info(f"hireiList データ発見: {len(data['hireiList'])}政党")
                            # 後で実装
                            break
                    except:
                        continue
        
        # 標準的なHTMLセレクターも試す
        candidate_blocks = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'candidate|person|member|senkyoku|hirei'))
        
        if candidate_blocks:
            logger.info(f"{party_name}: {len(candidate_blocks)}個のブロック発見")
            
            for i, block in enumerate(candidate_blocks):
                candidate_info = extract_candidate_info_from_block(block, party_name, page_url, i, collector)
                if candidate_info:
                    candidates.append(candidate_info)
        
        # 候補者データが見つからない場合、他の方法を試す
        if not candidates:
            # テキスト解析による候補者名抽出
            text_candidates = extract_candidates_from_text(html_content, party_name, page_url, collector)
            candidates.extend(text_candidates)
        
    except Exception as e:
        logger.debug(f"HTML解析エラー ({party_name}): {e}")
    
    return candidates

def extract_candidate_info_from_block(block, party_name, page_url, idx, collector):
    """ブロックから候補者情報を抽出"""
    try:
        # 正確なクラス名を使って名前を抽出
        name_ttl = block.select_one('.ttl, [class*="ttl"], .title, [class*="title"]')
        name_subttl = block.select_one('.subttl, [class*="subttl"], .subtitle, [class*="subtitle"]')
        
        # 名前（漢字）の取得
        if name_ttl:
            name = name_ttl.get_text(strip=True)
        else:
            # フォールバック: 他のセレクターを試す
            name_elem = block.select_one('h2, h3, h4, [class*="name"]')
            if name_elem:
                name = name_elem.get_text(strip=True)
            else:
                return None
        
        # 読み名（カタカナ）の取得
        name_kana = ""
        if name_subttl:
            name_kana = name_subttl.get_text(strip=True)
        
        # 不要なデータをフィルタリング
        invalid_names = [
            '会員登録', '比例代表予想', 'ログイン', 'サインアップ', 
            'MY選挙', '選挙区', 'この', 'コンテンツ', '予想される顔ぶれ',
            'について', 'シェア', 'ページ', '政党', '全政党',
            # 政党名をフィルタリング
            '自由民主党', '立憲民主党', '公明党', '日本維新の会', '日本共産党',
            '国民民主党', 'れいわ新選組', '参政党', '社会民主党', 
            '日本保守党', 'みんなでつくる党', 'NHK党', 'チームみらい',
            '再生の道', '日本改革党', '無所属連合', '日本誠真会',
            '比例代表', '全国比例', '代表者', '百田尚樹', '石濱哲信'
        ]
        
        if any(invalid in name for invalid in invalid_names):
            logger.debug(f"無効な名前をフィルタリング: {name}")
            return None
        
        # 日本人の名前として妥当かチェック
        if len(name) < 2 or len(name) > 10:
            return None
        
        # 漢字が含まれているかチェック
        if not re.search(r'[一-龯]', name):
            return None
        
        # プロフィールリンクを探す
        profile_link = block.find('a', href=re.compile(r'/seijika/\\d+'))
        profile_url = ""
        candidate_id = f"hirei_{party_name}_{idx}"
        detailed_info = {}
        
        if profile_link:
            href = profile_link.get('href', '')
            if href.startswith('/'):
                profile_url = f"https://go2senkyo.com{href}"
            else:
                profile_url = href
            
            # 候補者ID抽出
            match = re.search(r'/seijika/(\\d+)', href)
            if match:
                candidate_id = f"hirei_{match.group(1)}"
                
                # 個別プロフィールページから詳細情報を取得
                detailed_info = get_detailed_profile_info(profile_url, collector)
        
        candidate_data = {
            "candidate_id": candidate_id,
            "name": name,
            "prefecture": "比例代表",
            "constituency": "全国比例",
            "constituency_type": "proportional",
            "party": party_name,
            "party_normalized": collector.normalize_party_name(party_name),
            "profile_url": profile_url,
            "source_page": page_url,
            "source": "go2senkyo_proportional_v2",
            "collected_at": datetime.now().isoformat()
        }
        
        # カタカナ名前が存在する場合のみ追加
        if name_kana:
            candidate_data["name_kana"] = name_kana
        
        # 詳細情報をマージ
        candidate_data.update(detailed_info)
        
        return candidate_data
        
    except Exception as e:
        logger.debug(f"候補者抽出エラー ({party_name}): {e}")
        return None

def get_detailed_profile_info(profile_url, collector):
    """個別プロフィールページから詳細情報を取得"""
    detailed_info = {}
    
    try:
        if not profile_url:
            return detailed_info
        
        logger.debug(f"プロフィール詳細取得: {profile_url}")
        collector.random_delay(0.5, 1.0)  # 短い間隔
        
        response = collector.session.get(profile_url, timeout=15)
        if response.status_code != 200:
            return detailed_info
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # p_seijika_profle_data_sitelist クラスからサイト情報を取得
        sitelist_elem = soup.find(class_='p_seijika_profle_data_sitelist')
        if sitelist_elem:
            site_links = sitelist_elem.find_all('a', href=True)
            websites = []
            for link in site_links:
                url = link.get('href', '')
                title = link.get_text(strip=True)
                if url and title:
                    websites.append({"url": url, "title": title})
            
            if websites:
                detailed_info["websites"] = websites
                # 公式サイト（最初のリンク）を別途保存
                detailed_info["official_website"] = websites[0]["url"]
        
        # 年齢情報
        age_elem = soup.find(string=re.compile(r'(\d+)歳'))
        if age_elem:
            age_match = re.search(r'(\d+)歳', age_elem)
            if age_match:
                detailed_info["age_info"] = age_match.group(1)
        
        # 職業・肩書き
        occupation_selectors = [
            '.occupation', '.job', '.title', 
            '[class*="occupation"]', '[class*="job"]'
        ]
        for selector in occupation_selectors:
            elem = soup.select_one(selector)
            if elem:
                occupation = elem.get_text(strip=True)
                if occupation and len(occupation) < 50:
                    detailed_info["occupation"] = occupation
                break
        
        # 経歴・プロフィール
        profile_selectors = [
            '.profile', '.career', '.history', '.bio',
            '[class*="profile"]', '[class*="career"]', '[class*="history"]'
        ]
        for selector in profile_selectors:
            elem = soup.select_one(selector)
            if elem:
                career = elem.get_text(strip=True)
                if career and len(career) > 20:  # 意味のある経歴情報のみ
                    detailed_info["career"] = career[:500]  # 500文字まで
                break
        
        # 出身地
        birthplace_elem = soup.find(string=re.compile(r'出身.*[都道府県市区町村]'))
        if birthplace_elem:
            birthplace_match = re.search(r'出身[：:]*([都道府県市区町村\w]+)', birthplace_elem)
            if birthplace_match:
                detailed_info["birthplace"] = birthplace_match.group(1)
        
        logger.debug(f"詳細情報取得完了: {len(detailed_info)}項目")
        
    except Exception as e:
        logger.debug(f"プロフィール詳細取得エラー: {e}")
    
    return detailed_info

def extract_candidates_from_text(html_content, party_name, page_url, collector):
    """HTMLテキストから候補者名を抽出（フォールバック）"""
    candidates = []
    
    try:
        # HTMLタグを除去
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        
        # 不要なデータを事前にフィルタリング
        invalid_names = [
            '会員登録', '比例代表予想', 'ログイン', 'サインアップ', 
            'MY選挙', '選挙区', 'この', 'コンテンツ', '予想される顔ぶれ',
            'について', 'シェア', 'ページ', '政党', '全政党', 'について',
            'このページ', 'をシェア', 'する'
        ]
        
        # 日本人の名前パターンを探す
        name_patterns = [
            r'([一-龯]{2,4}[\\s　]*[一-龯]{2,8})',  # 漢字のみ
            r'([一-龯]{2,4}[\\s　]*[一-龯]{2,8}[ァ-ヶ]+)',  # 漢字 + カタカナ
        ]
        
        found_names = set()
        for pattern in name_patterns:
            matches = re.finditer(pattern, text)
            for i, match in enumerate(matches):
                full_name = match.group(1).strip()
                
                # 基本的なフィルタリング
                if len(full_name) < 2 or len(full_name) > 10:
                    continue
                
                # 不要なテキストをフィルタリング
                if any(invalid in full_name for invalid in invalid_names):
                    continue
                
                # 重複チェック
                if full_name in found_names:
                    continue
                
                # 漢字が含まれているかチェック
                if not re.search(r'[一-龯]', full_name):
                    continue
                
                found_names.add(full_name)
                
                # 名前とカタカナを分離
                name, name_kana = collector.separate_name_and_kana(full_name)
                
                candidate_data = {
                    "candidate_id": f"hirei_text_{party_name}_{i}",
                    "name": name,
                    "prefecture": "比例代表",
                    "constituency": "全国比例", 
                    "constituency_type": "proportional",
                    "party": party_name,
                    "party_normalized": collector.normalize_party_name(party_name),
                    "profile_url": "",
                    "source_page": page_url,
                    "source": "go2senkyo_proportional_text_extraction",
                    "collected_at": datetime.now().isoformat()
                }
                
                if name_kana:
                    candidate_data["name_kana"] = name_kana
                
                candidates.append(candidate_data)
        
        # 候補者データが見つかった場合のみログ出力
        if candidates:
            logger.info(f"{party_name} テキスト抽出: {len(candidates)}名")
        
    except Exception as e:
        logger.debug(f"テキスト抽出エラー ({party_name}): {e}")
    
    return candidates

def merge_with_constituency_data_v2():
    """選挙区データと比例代表データを統合 v2"""
    logger.info("🔗 選挙区データと比例代表データを統合 v2...")
    
    try:
        # 比例代表データ収集
        proportional_candidates = collect_proportional_v2()
        
        # 既存の選挙区データ読み込み
        data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
        latest_file = data_dir / "go2senkyo_optimized_latest.json"
        
        if latest_file.exists():
            with open(latest_file, 'r', encoding='utf-8') as f:
                constituency_data = json.load(f)
                constituency_candidates = constituency_data.get('data', [])
        else:
            constituency_candidates = []
        
        # データ統合
        all_candidates = constituency_candidates + proportional_candidates
        
        logger.info(f"📊 統合結果 v2:")
        logger.info(f"  選挙区候補者: {len(constituency_candidates)}名")
        logger.info(f"  比例代表候補者: {len(proportional_candidates)}名")
        logger.info(f"  総候補者数: {len(all_candidates)}名")
        
        # 統合データ保存
        if proportional_candidates:  # 比例代表データがある場合のみ保存
            save_merged_data_v2(all_candidates, data_dir)
        else:
            logger.warning("比例代表データが収集できなかったため、データ統合をスキップします")
        
        return all_candidates
        
    except Exception as e:
        logger.error(f"❌ データ統合エラー v2: {e}")
        raise

def save_merged_data_v2(candidates, output_dir):
    """統合データの保存 v2"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    main_file = output_dir / f"go2senkyo_merged_v2_{timestamp}.json"
    latest_file = output_dir / "go2senkyo_optimized_latest.json"
    
    # 統計計算
    party_stats = {}
    constituency_stats = {}
    
    for candidate in candidates:
        party = candidate.get('party', '無所属')
        constituency_type = candidate.get('constituency_type', 'unknown')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        constituency_stats[constituency_type] = constituency_stats.get(constituency_type, 0) + 1
    
    save_data = {
        "metadata": {
            "data_type": "go2senkyo_merged_sangiin_2025_v2",
            "collection_method": "constituency_and_proportional_scraping_v2",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
            "coverage": {
                "constituency_types": len(constituency_stats),
                "parties": len(party_stats)
            },
            "collection_stats": {
                "total_candidates": len(candidates),
                "detailed_profiles": 0,
                "with_photos": 0,
                "with_policies": 0,
                "errors": 0
            },
            "quality_metrics": {
                "detail_coverage": "0%",
                "photo_coverage": "0%",
                "policy_coverage": "0%"
            }
        },
        "statistics": {
            "by_party": party_stats,
            "by_constituency_type": constituency_stats
        },
        "data": candidates
    }
    
    # ファイル保存
    with open(main_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 統合データ保存完了 v2: {main_file}")

if __name__ == "__main__":
    merge_with_constituency_data_v2()