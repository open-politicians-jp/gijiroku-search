#!/usr/bin/env python3
"""
Go2senkyo.com参議院選2025データ収集（選挙区別強化版）

https://sangiin.go2senkyo.com/2025/prefecture/{prefecture_code} 
各都道府県選挙区の詳細データ収集と候補者個別ページスクレイピング

機能:
- 都道府県別選挙区データ収集
- 候補者詳細ページからの包括的情報取得
- HP、SNS、政策・マニフェスト収集
- プロフィール写真・経歴情報
- リアルタイム選挙情勢データ
"""

import json
import requests
import time
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse, parse_qs

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Go2senkyoEnhancedCollector:
    """Go2senkyo.com 参院選2025強化データ収集クラス"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.output_dir = self.project_root / "frontend" / "public" / "data" / "sangiin_candidates"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Go2senkyo基本URL設定
        self.base_url = "https://sangiin.go2senkyo.com"
        self.sangiin_2025_url = f"{self.base_url}/2025"
        
        # 都道府県コードマッピング（Go2senkyo用）
        self.prefecture_codes = {
            "北海道": 1, "青森県": 2, "岩手県": 3, "宮城県": 4, "秋田県": 5,
            "山形県": 6, "福島県": 7, "茨城県": 8, "栃木県": 9, "群馬県": 10,
            "埼玉県": 11, "千葉県": 12, "東京都": 13, "神奈川県": 14, "新潟県": 15,
            "富山県": 16, "石川県": 17, "福井県": 18, "山梨県": 19, "長野県": 20,
            "岐阜県": 21, "静岡県": 22, "愛知県": 23, "三重県": 24, "滋賀県": 25,
            "京都府": 26, "大阪府": 27, "兵庫県": 28, "奈良県": 29, "和歌山県": 30,
            "鳥取県": 31, "島根県": 32, "岡山県": 33, "広島県": 34, "山口県": 35,
            "徳島県": 36, "香川県": 37, "愛媛県": 38, "高知県": 39, "福岡県": 40,
            "佐賀県": 41, "長崎県": 42, "熊本県": 43, "大分県": 44, "宮崎県": 45,
            "鹿児島県": 46, "沖縄県": 47
        }
        
        # 改選議席数（2025年参院選）
        self.sangiin_seats = {
            "北海道": 1, "青森県": 1, "岩手県": 1, "宮城県": 1, "秋田県": 1,
            "山形県": 1, "福島県": 1, "茨城県": 2, "栃木県": 1, "群馬県": 1,
            "埼玉県": 3, "千葉県": 3, "東京都": 6, "神奈川県": 4, "新潟県": 1,
            "富山県": 1, "石川県": 1, "福井県": 1, "山梨県": 1, "長野県": 1,
            "岐阜県": 1, "静岡県": 2, "愛知県": 4, "三重県": 1, "滋賀県": 1,
            "京都府": 2, "大阪府": 4, "兵庫県": 3, "奈良県": 1, "和歌山県": 1,
            "鳥取県": 1, "島根県": 1, "岡山県": 1, "広島県": 2, "山口県": 1,
            "徳島県": 1, "香川県": 1, "愛媛県": 1, "高知県": 1, "福岡県": 3,
            "佐賀県": 1, "長崎県": 1, "熊本県": 1, "大分県": 1, "宮崎県": 1,
            "鹿児島県": 1, "沖縄県": 1
        }
        
        # 収集統計
        self.stats = {
            "total_candidates": 0,
            "with_detailed_info": 0,
            "with_photos": 0,
            "with_policies": 0,
            "with_sns": 0,
            "prefectures_processed": 0,
            "errors": 0
        }
    
    def update_headers(self):
        """User-Agent更新とブラウザ偽装"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Cache-Control': 'no-cache',
            'Referer': self.base_url
        })
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """ランダム遅延（Go2senkyo負荷軽減）"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def collect_all_prefectures(self) -> List[Dict[str, Any]]:
        """全都道府県の参院選候補者データを収集"""
        logger.info("🚀 Go2senkyo 全都道府県参院選2025データ収集開始...")
        
        all_candidates = []
        
        # 主要都道府県を優先的に処理
        priority_prefectures = ["東京都", "大阪府", "神奈川県", "愛知県", "埼玉県", "千葉県", "兵庫県", "福岡県"]
        other_prefectures = [pref for pref in self.prefecture_codes.keys() if pref not in priority_prefectures]
        
        processing_order = priority_prefectures + other_prefectures
        
        for prefecture in processing_order:
            try:
                logger.info(f"📍 {prefecture} データ収集中...")
                pref_candidates = self.collect_prefecture_candidates(prefecture)
                
                if pref_candidates:
                    all_candidates.extend(pref_candidates)
                    self.stats["prefectures_processed"] += 1
                    logger.info(f"✅ {prefecture}: {len(pref_candidates)}名収集")
                else:
                    logger.warning(f"⚠️ {prefecture}: データ収集失敗")
                
                # 都道府県間の間隔
                self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"❌ {prefecture}エラー: {str(e)}")
                self.stats["errors"] += 1
                continue
        
        logger.info(f"🎯 全都道府県収集完了: {len(all_candidates)}名")
        self.stats["total_candidates"] = len(all_candidates)
        
        return all_candidates
    
    def collect_prefecture_candidates(self, prefecture: str) -> List[Dict[str, Any]]:
        """都道府県別候補者データ収集"""
        pref_code = self.prefecture_codes.get(prefecture)
        if not pref_code:
            logger.warning(f"都道府県コードが見つかりません: {prefecture}")
            return []
        
        prefecture_url = f"{self.sangiin_2025_url}/prefecture/{pref_code}"
        
        try:
            self.random_delay()
            response = self.session.get(prefecture_url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"{prefecture}ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            candidates = self.parse_prefecture_page(soup, prefecture, prefecture_url)
            
            # 各候補者の詳細情報を取得
            enhanced_candidates = []
            for candidate in candidates:
                try:
                    enhanced = self.enhance_candidate_details(candidate)
                    enhanced_candidates.append(enhanced)
                    self.random_delay(1, 2)  # 候補者詳細取得間隔
                    
                except Exception as e:
                    logger.debug(f"候補者{candidate.get('name', 'unknown')}詳細取得エラー: {e}")
                    enhanced_candidates.append(candidate)
                    continue
            
            return enhanced_candidates
            
        except Exception as e:
            logger.error(f"{prefecture}データ収集エラー: {str(e)}")
            return []
    
    def parse_prefecture_page(self, soup: BeautifulSoup, prefecture: str, page_url: str) -> List[Dict[str, Any]]:
        """都道府県ページから候補者基本情報を抽出"""
        candidates = []
        
        try:
            # Go2senkyoの候補者リスト要素を探す
            candidate_selectors = [
                '.candidate-item',
                '.candidate-card', 
                '.person-item',
                '[class*="candidate"]',
                '[class*="person"]'
            ]
            
            candidate_elements = []
            for selector in candidate_selectors:
                elements = soup.select(selector)
                if elements:
                    candidate_elements = elements
                    logger.debug(f"候補者要素発見: {selector} ({len(elements)}件)")
                    break
            
            # より汎用的な探索
            if not candidate_elements:
                # 名前パターンでの探索
                name_pattern = re.compile(r'[一-龯]{2,4}[\s　]+[一-龯]{2,8}')
                potential_candidates = soup.find_all(['div', 'li', 'article'], string=name_pattern)
                
                if not potential_candidates:
                    # リンクから候補者ページを探す
                    candidate_links = soup.find_all('a', href=re.compile(r'candidate|person|profile'))
                    for link in candidate_links:
                        name_text = link.get_text(strip=True)
                        if name_pattern.search(name_text):
                            potential_candidates.append(link)
                
                candidate_elements = potential_candidates[:20]  # 最大20名まで
            
            for idx, element in enumerate(candidate_elements):
                try:
                    candidate_data = self.extract_candidate_basic_info(element, prefecture, page_url, idx)
                    if candidate_data:
                        candidates.append(candidate_data)
                        
                except Exception as e:
                    logger.debug(f"候補者要素{idx}解析エラー: {e}")
                    continue
            
            logger.info(f"{prefecture}: {len(candidates)}名の基本情報取得")
            
        except Exception as e:
            logger.error(f"{prefecture}ページ解析エラー: {str(e)}")
        
        return candidates
    
    def extract_candidate_basic_info(self, element, prefecture: str, page_url: str, idx: int) -> Optional[Dict[str, Any]]:
        """候補者要素から基本情報を抽出"""
        try:
            # 候補者名の抽出
            name = ""
            name_selectors = ['h2', 'h3', 'h4', '.name', '.candidate-name', 'a']
            
            for selector in name_selectors:
                name_elem = element.select_one(selector) if hasattr(element, 'select_one') else element.find(selector)
                if name_elem:
                    text = name_elem.get_text(strip=True)
                    name_match = re.search(r'([一-龯]{2,4}[\s　]+[一-龯]{2,8})', text)
                    if name_match:
                        name = name_match.group(1).strip().replace('\u3000', ' ')
                        break
            
            if not name:
                # 要素全体のテキストから名前を探す
                full_text = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)
                name_match = re.search(r'([一-龯]{2,4}[\s　]+[一-龯]{2,8})', full_text)
                if name_match:
                    name = name_match.group(1).strip().replace('\u3000', ' ')
            
            if not name:
                return None
            
            # 政党情報の抽出
            party = ""
            party_keywords = ['自民', '立憲', '維新', '公明', '共産', '国民', 'れいわ', '社民', 'N国', 'NHK', '無所属']
            
            for keyword in party_keywords:
                if keyword in element.get_text() if hasattr(element, 'get_text') else str(element):
                    party_mapping = {
                        '自民': '自由民主党', '立憲': '立憲民主党', '維新': '日本維新の会',
                        '公明': '公明党', '共産': '日本共産党', '国民': '国民民主党',
                        'れいわ': 'れいわ新選組', '社民': '社会民主党', 
                        'N国': 'NHK党', 'NHK': 'NHK党', '無所属': '無所属'
                    }
                    party = party_mapping.get(keyword, keyword)
                    break
            
            if not party:
                party = "未分類"
            
            # 詳細ページURLの抽出
            detail_url = ""
            if hasattr(element, 'find'):
                link_elem = element.find('a', href=True)
                if link_elem:
                    href = link_elem['href']
                    if href.startswith('/'):
                        detail_url = urljoin(self.base_url, href)
                    elif href.startswith('http'):
                        detail_url = href
            elif hasattr(element, 'get') and element.get('href'):
                href = element.get('href')
                if href.startswith('/'):
                    detail_url = urljoin(self.base_url, href)
                elif href.startswith('http'):
                    detail_url = href
            
            # 候補者ID生成
            candidate_id = f"go2senkyo_{prefecture.replace('都', '').replace('府', '').replace('県', '')}_{idx+1:03d}"
            
            candidate_data = {
                "candidate_id": candidate_id,
                "name": name,
                "prefecture": prefecture,
                "constituency": prefecture.replace('都', '').replace('府', '').replace('県', ''),
                "constituency_type": "single_member",
                "party": party,
                "party_normalized": party,
                "detail_url": detail_url,
                "source_page": page_url,
                "source": "go2senkyo_enhanced",
                "collected_at": datetime.now().isoformat(),
                "seats_contested": self.sangiin_seats.get(prefecture, 1)
            }
            
            return candidate_data
            
        except Exception as e:
            logger.debug(f"候補者基本情報抽出エラー: {e}")
            return None
    
    def enhance_candidate_details(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """候補者詳細ページから包括的情報を取得"""
        enhanced = candidate.copy()
        detail_url = candidate.get('detail_url', '')
        
        if not detail_url:
            return enhanced
        
        try:
            logger.debug(f"候補者詳細取得: {candidate.get('name', 'unknown')} - {detail_url}")
            
            self.random_delay(1, 2)
            response = self.session.get(detail_url, timeout=20)
            
            if response.status_code != 200:
                logger.debug(f"詳細ページアクセス失敗: {detail_url}")
                return enhanced
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # プロフィール情報の抽出
            profile_data = self.extract_profile_details(soup, detail_url)
            enhanced.update(profile_data)
            
            # 政策・マニフェスト情報
            policy_data = self.extract_policy_information(soup)
            enhanced.update(policy_data)
            
            # SNS・Webサイト情報
            social_data = self.extract_social_links(soup)
            enhanced.update(social_data)
            
            # 写真・画像
            photo_data = self.extract_candidate_photos(soup, detail_url)
            enhanced.update(photo_data)
            
            # 統計更新
            if profile_data or policy_data or social_data or photo_data:
                self.stats["with_detailed_info"] += 1
            if photo_data.get('photo_url'):
                self.stats["with_photos"] += 1
            if policy_data.get('manifesto_summary'):
                self.stats["with_policies"] += 1
            if social_data.get('sns_accounts'):
                self.stats["with_sns"] += 1
            
        except Exception as e:
            logger.debug(f"候補者詳細取得エラー ({candidate.get('name', 'unknown')}): {e}")
        
        return enhanced
    
    def extract_profile_details(self, soup: BeautifulSoup, page_url: str) -> Dict[str, Any]:
        """プロフィール詳細情報の抽出"""
        profile = {}
        
        try:
            # 年齢・生年月日
            age_patterns = [
                re.compile(r'(\d{1,2})歳'),
                re.compile(r'([昭平令]\w+\d+年)'),
                re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日)')
            ]
            
            page_text = soup.get_text()
            for pattern in age_patterns:
                match = pattern.search(page_text)
                if match:
                    profile['age_info'] = match.group(1)
                    break
            
            # 経歴・学歴
            career_keywords = ['経歴', '学歴', 'プロフィール', '略歴', '出身']
            for keyword in career_keywords:
                career_section = soup.find(string=re.compile(keyword))
                if career_section and career_section.parent:
                    career_text = career_section.parent.get_text(strip=True)
                    if len(career_text) > 50:
                        profile['career'] = career_text[:800]
                        break
            
            # 職業・肩書き
            title_keywords = ['職業', '現職', '肩書', '役職']
            for keyword in title_keywords:
                title_section = soup.find(string=re.compile(keyword))
                if title_section and title_section.parent:
                    title_text = title_section.parent.get_text(strip=True)
                    profile['occupation'] = title_text[:200]
                    break
            
            # 出身地
            origin_patterns = [
                re.compile(r'([都道府県][市区町村]+)出身'),
                re.compile(r'出身[：:]\s*([都道府県][市区町村]+)'),
            ]
            
            for pattern in origin_patterns:
                match = pattern.search(page_text)
                if match:
                    profile['birthplace'] = match.group(1)
                    break
        
        except Exception as e:
            logger.debug(f"プロフィール抽出エラー: {e}")
        
        return profile
    
    def extract_policy_information(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """政策・マニフェスト情報の抽出"""
        policy = {}
        
        try:
            # 政策キーワード検索
            policy_keywords = ['政策', 'マニフェスト', '公約', '主張', '政治信条', '取り組み', '重点政策']
            policy_texts = []
            
            for keyword in policy_keywords:
                # キーワードを含む要素を探す
                policy_elements = soup.find_all(string=re.compile(keyword))
                
                for element in policy_elements:
                    if element.parent:
                        parent_text = element.parent.get_text(strip=True)
                        if len(parent_text) > 30:
                            policy_texts.append(parent_text)
                
                # 十分な情報が集まったら停止
                if len(' '.join(policy_texts)) > 500:
                    break
            
            if policy_texts:
                combined_policy = ' '.join(policy_texts)
                # 重複除去と整理
                unique_sentences = []
                for sentence in combined_policy.split('。'):
                    if sentence.strip() and sentence not in unique_sentences:
                        unique_sentences.append(sentence.strip())
                
                policy['manifesto_summary'] = '。'.join(unique_sentences[:10])[:1000]
            
            # 重点分野の抽出
            policy_areas = ['経済', '外交', '安全保障', '教育', '環境', '社会保障', '医療', '農業']
            mentioned_areas = []
            
            page_text = soup.get_text().lower()
            for area in policy_areas:
                if area in page_text:
                    mentioned_areas.append(area)
            
            if mentioned_areas:
                policy['policy_areas'] = mentioned_areas
        
        except Exception as e:
            logger.debug(f"政策情報抽出エラー: {e}")
        
        return policy
    
    def extract_social_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """SNS・Webサイトリンクの抽出"""
        social = {"sns_accounts": {}, "websites": []}
        
        try:
            # すべてのリンクをチェック
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href'].lower()
                
                # Twitter/X
                if 'twitter.com' in href or 'x.com' in href:
                    social["sns_accounts"]["twitter"] = link['href']
                
                # Facebook
                elif 'facebook.com' in href:
                    social["sns_accounts"]["facebook"] = link['href']
                
                # Instagram
                elif 'instagram.com' in href:
                    social["sns_accounts"]["instagram"] = link['href']
                
                # YouTube
                elif 'youtube.com' in href or 'youtu.be' in href:
                    social["sns_accounts"]["youtube"] = link['href']
                
                # TikTok
                elif 'tiktok.com' in href:
                    social["sns_accounts"]["tiktok"] = link['href']
                
                # 公式ウェブサイト
                elif any(domain in href for domain in ['.com', '.jp', '.org', '.net']) and \
                     not any(exclude in href for exclude in ['twitter', 'facebook', 'instagram', 'youtube', 'go2senkyo']):
                    if len(social["websites"]) < 3:  # 最大3つまで
                        social["websites"].append({
                            "url": link['href'],
                            "title": link.get_text(strip=True)[:50]
                        })
            
            # ウェブサイト情報をメインに移動
            if social["websites"]:
                social["official_website"] = social["websites"][0]["url"]
        
        except Exception as e:
            logger.debug(f"SNS・リンク抽出エラー: {e}")
        
        return social
    
    def extract_candidate_photos(self, soup: BeautifulSoup, page_url: str) -> Dict[str, Any]:
        """候補者写真・画像の抽出"""
        photos = {}
        
        try:
            # プロフィール写真の候補
            img_selectors = [
                'img[alt*="プロフィール"]',
                'img[alt*="候補者"]',
                'img[alt*="写真"]',
                '.profile-image img',
                '.candidate-photo img',
                '.person-image img'
            ]
            
            photo_candidates = []
            
            for selector in img_selectors:
                imgs = soup.select(selector)
                photo_candidates.extend(imgs)
            
            # より汎用的な画像検索
            if not photo_candidates:
                all_imgs = soup.find_all('img')
                for img in all_imgs:
                    alt = img.get('alt', '').lower()
                    src = img.get('src', '').lower()
                    
                    # プロフィール画像の可能性が高いもの
                    if any(keyword in alt for keyword in ['profile', 'candidate', '候補', 'person']) or \
                       any(keyword in src for keyword in ['profile', 'candidate', '候補', 'person']):
                        photo_candidates.append(img)
            
            # 最適な写真を選択
            if photo_candidates:
                best_photo = photo_candidates[0]
                src = best_photo.get('src', '')
                
                if src:
                    if src.startswith('/'):
                        photo_url = urljoin(page_url, src)
                    elif src.startswith('http'):
                        photo_url = src
                    else:
                        photo_url = urljoin(page_url, '/' + src)
                    
                    photos['photo_url'] = photo_url
                    photos['photo_alt'] = best_photo.get('alt', '')
        
        except Exception as e:
            logger.debug(f"写真抽出エラー: {e}")
        
        return photos
    
    def save_enhanced_data(self, candidates: List[Dict[str, Any]]):
        """強化されたデータの保存"""
        if not candidates:
            logger.warning("保存する候補者データがありません")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # メインファイル
        main_file = self.output_dir / f"go2senkyo_enhanced_{timestamp}.json"
        latest_file = self.output_dir / "go2senkyo_enhanced_latest.json"
        
        # 統計情報の計算
        party_stats = {}
        prefecture_stats = {}
        
        for candidate in candidates:
            party = candidate.get('party', '無所属')
            prefecture = candidate.get('prefecture', '未分類')
            
            party_stats[party] = party_stats.get(party, 0) + 1
            prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
        
        # 保存データ構造
        save_data = {
            "metadata": {
                "data_type": "go2senkyo_enhanced_sangiin_2025",
                "collection_method": "prefecture_by_prefecture_scraping",
                "total_candidates": len(candidates),
                "generated_at": datetime.now().isoformat(),
                "source_site": "sangiin.go2senkyo.com",
                "collection_stats": self.stats,
                "data_quality": {
                    "detailed_info_rate": f"{(self.stats['with_detailed_info']/max(len(candidates), 1)*100):.1f}%",
                    "photo_rate": f"{(self.stats['with_photos']/max(len(candidates), 1)*100):.1f}%",
                    "policy_rate": f"{(self.stats['with_policies']/max(len(candidates), 1)*100):.1f}%",
                    "sns_rate": f"{(self.stats['with_sns']/max(len(candidates), 1)*100):.1f}%"
                }
            },
            "statistics": {
                "by_party": party_stats,
                "by_prefecture": prefecture_stats
            },
            "data": candidates
        }
        
        # ファイル保存
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Go2senkyo強化データ保存完了:")
        logger.info(f"  - ファイル: {main_file}")
        logger.info(f"  - 候補者数: {len(candidates)}名")
        logger.info(f"  - 処理都道府県: {self.stats['prefectures_processed']}")
        
        # 詳細統計表示
        self.display_final_stats(candidates, party_stats, prefecture_stats)
    
    def display_final_stats(self, candidates: List[Dict[str, Any]], 
                           party_stats: Dict[str, int], 
                           prefecture_stats: Dict[str, int]):
        """最終統計の表示"""
        logger.info("\n" + "="*60)
        logger.info("📊 Go2senkyo 参院選2025 強化データ収集結果")
        logger.info("="*60)
        
        logger.info(f"🎯 総収集数: {len(candidates)}名")
        logger.info(f"📍 処理都道府県: {self.stats['prefectures_processed']}")
        logger.info(f"📋 詳細情報付き: {self.stats['with_detailed_info']}名")
        logger.info(f"📷 写真付き: {self.stats['with_photos']}名")
        logger.info(f"📜 政策情報付き: {self.stats['with_policies']}名")
        logger.info(f"🔗 SNS情報付き: {self.stats['with_sns']}名")
        logger.info(f"❌ エラー数: {self.stats['errors']}")
        
        # 政党別トップ10
        logger.info("\n🏛️ 政党別候補者数 (トップ10):")
        top_parties = sorted(party_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for party, count in top_parties:
            logger.info(f"  {party}: {count}名")
        
        # 都道府県別トップ10
        logger.info("\n🗾 都道府県別候補者数 (トップ10):")
        top_prefectures = sorted(prefecture_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for prefecture, count in top_prefectures:
            logger.info(f"  {prefecture}: {count}名")

def main():
    """メイン実行関数"""
    logger.info("🚀 Go2senkyo参院選2025強化データ収集開始...")
    
    collector = Go2senkyoEnhancedCollector()
    
    try:
        # 全都道府県のデータ収集
        all_candidates = collector.collect_all_prefectures()
        
        if not all_candidates:
            logger.error("❌ 候補者データを収集できませんでした")
            return
        
        # データ保存
        collector.save_enhanced_data(all_candidates)
        
        logger.info("✨ Go2senkyo強化データ収集完了")
        
    except KeyboardInterrupt:
        logger.info("⚠️ ユーザーによる中断")
    except Exception as e:
        logger.error(f"❌ メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()