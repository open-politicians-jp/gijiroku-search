#!/usr/bin/env python3
"""
Go2senkyo 最適化データ収集スクリプト

HTML構造分析結果を基に、効率的に候補者データを収集
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
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Go2senkyoOptimizedCollector:
    """Go2senkyo 最適化データ収集クラス"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # URL設定 (update_headersで使用されるため先に設定)
        self.base_url = "https://sangiin.go2senkyo.com"
        self.profile_base_url = "https://go2senkyo.com"
        
        # ヘッダー初期化 (base_url設定後)
        self.update_headers()
        
        # 出力ディレクトリ
        self.project_root = Path(__file__).parent.parent.parent
        self.output_dir = self.project_root / "frontend" / "public" / "data" / "sangiin_candidates"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 優先処理する主要都道府県
        self.priority_prefectures = {
            "東京都": 13, "大阪府": 27, "神奈川県": 14, "愛知県": 23, 
            "埼玉県": 11, "千葉県": 12, "兵庫県": 28, "福岡県": 40
        }
        
        # 統計
        self.stats = {
            "total_candidates": 0,
            "detailed_profiles": 0,
            "with_photos": 0,
            "with_policies": 0,
            "errors": 0
        }
    
    def update_headers(self):
        """ヘッダー更新 (デスクトップブラウザ優先、Referer削除)"""
        # デスクトップブラウザ User-Agent 強制使用
        desktop_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        self.session.headers.update({
            'User-Agent': desktop_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
            # Refererヘッダー削除 - サーバーで異なるバージョンを返す原因
        })
    
    def random_delay(self, min_sec=1, max_sec=3):
        """ランダム遅延"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def separate_name_and_kana(self, full_name: str) -> tuple:
        """名前とカタカナを分離"""
        try:
            # パターン1: 漢字とカタカナが混在 (例: "山田太郎ヤマダタロウ")
            if re.search(r'[一-龯]+[ァ-ヶ]+', full_name):
                match = re.match(r'([一-龯\s]+)([ァ-ヶ\s]+)', full_name)
                if match:
                    name = match.group(1).strip()
                    kana = match.group(2).strip()
                    return name, kana
            
            # パターン2: スペースで分離 (例: "山田太郎 ヤマダタロウ")
            if ' ' in full_name and re.search(r'[ァ-ヶ]', full_name):
                parts = full_name.split()
                if len(parts) >= 2:
                    name_part = parts[0]
                    kana_part = parts[1] if re.search(r'[ァ-ヶ]', parts[1]) else ''
                    if kana_part:
                        return name_part, kana_part
            
            # パターン3: カタカナのみの場合は名前として扱う
            if re.match(r'^[ァ-ヶ\s]+$', full_name):
                return full_name, ''
            
            # パターン4: 漢字のみまたは混合の場合
            return full_name, ''
            
        except Exception as e:
            logger.debug(f"名前分離エラー: {e}")
            return full_name, ''
    
    def collect_priority_prefectures(self) -> List[Dict[str, Any]]:
        """주요 도도부현 후보자 수집"""
        logger.info("🚀 주요 도도부현 후보자 데이터 수집 시작...")
        
        all_candidates = []
        
        for prefecture, code in self.priority_prefectures.items():
            try:
                logger.info(f"📍 {prefecture} (코드: {code}) 처리 중...")
                candidates = self.collect_prefecture_data(prefecture, code)
                
                if candidates:
                    all_candidates.extend(candidates)
                    logger.info(f"✅ {prefecture}: {len(candidates)}명 수집")
                else:
                    logger.warning(f"⚠️ {prefecture}: 후보자 없음")
                
                self.random_delay(2, 4)  # 도도부현 간 딜레이
                
            except Exception as e:
                logger.error(f"❌ {prefecture} 에러: {e}")
                self.stats["errors"] += 1
                continue
        
        logger.info(f"🎯 주요 도도부현 수집 완료: {len(all_candidates)}명")
        self.stats["total_candidates"] = len(all_candidates)
        
        return all_candidates
    
    def collect_prefecture_data(self, prefecture: str, code: int) -> List[Dict[str, Any]]:
        """특정 도도부현의 후보자 데이터 수집"""
        url = f"{self.base_url}/2025/prefecture/{code}"
        
        try:
            self.random_delay()
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"{prefecture} 페이지 접근 실패: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            candidates = self.parse_candidate_list(soup, prefecture, url)
            
            # 후보자 세부 정보 수집
            enhanced_candidates = []
            for candidate in candidates:
                try:
                    enhanced = self.enhance_candidate_profile(candidate)
                    enhanced_candidates.append(enhanced)
                    self.random_delay(1, 2)  # 프로필 수집 간격
                    
                except Exception as e:
                    logger.debug(f"후보자 {candidate.get('name', 'unknown')} 세부정보 에러: {e}")
                    enhanced_candidates.append(candidate)
                    continue
            
            return enhanced_candidates
            
        except Exception as e:
            logger.error(f"{prefecture} 데이터 수집 에러: {e}")
            return []
    
    def parse_candidate_list(self, soup: BeautifulSoup, prefecture: str, page_url: str) -> List[Dict[str, Any]]:
        """후보자 리스트 파싱 (구조 분석 결과 활용)"""
        candidates = []
        
        try:
            # 분석 결과를 기반으로 정확한 선택자 사용
            # 1. 주요 방법: 후보자 블록에서 추출
            candidate_blocks = soup.find_all('div', class_='p_senkyoku_list_block')
            logger.info(f"{prefecture}: {len(candidate_blocks)}개 후보자 블록 발견")
            
            for i, block in enumerate(candidate_blocks):
                try:
                    candidate_info = self.extract_candidate_from_block(block, prefecture, page_url, i)
                    if candidate_info:
                        candidates.append(candidate_info)
                except Exception as e:
                    logger.debug(f"블록 {i} 파싱 에러: {e}")
                    continue
            
            # 2. 백업: 프로필 링크에서 직접 추출
            if not candidates:
                profile_links = soup.find_all('a', href=re.compile(r'/seijika/\d+'))
                logger.debug(f"{prefecture}: {len(profile_links)}개 프로필 링크 발견")
                
                for i, link in enumerate(profile_links):
                    try:
                        candidate_info = self.extract_candidate_from_link(link, prefecture, page_url, i)
                        if candidate_info:
                            candidates.append(candidate_info)
                    except Exception as e:
                        logger.debug(f"링크 {i} 파싱 에러: {e}")
                        continue
            
            logger.info(f"{prefecture}: {len(candidates)}명 기본 정보 추출")
            
        except Exception as e:
            logger.error(f"{prefecture} 후보자 리스트 파싱 에러: {e}")
        
        return candidates
    
    def extract_candidate_from_link(self, link, prefecture: str, page_url: str, idx: int) -> Optional[Dict[str, Any]]:
        """프로필 링크에서 후보자 정보 추출"""
        try:
            href = link.get('href', '')
            if not href:
                return None
            
            # 프로필 URL 생성
            if href.startswith('/'):
                profile_url = urljoin(self.profile_base_url, href)
            else:
                profile_url = href
            
            # 후보자 ID 추출
            match = re.search(r'/seijika/(\d+)', href)
            candidate_id = match.group(1) if match else f"{prefecture}_{idx}"
            
            # 주변 요소에서 이름과 정당 정보 찾기
            name = ""
            party = ""
            
            # 링크 텍스트 확인
            link_text = link.get_text(strip=True)
            if link_text and link_text != "詳細・プロフィール":
                name = link_text
            
            # 부모/형제 요소에서 이름 찾기
            if not name:
                parent = link.parent
                while parent and not name:
                    # 이름 패턴 찾기
                    name_elem = parent.find(class_=re.compile(r'name|candidate'))
                    if name_elem:
                        name_text = name_elem.get_text(strip=True)
                        name_match = re.search(r'([一-龯]{2,4}[\s　]+[一-龯]{2,8})', name_text)
                        if name_match:
                            name = name_match.group(1).strip().replace('\u3000', ' ')
                            break
                    
                    # 상위 요소로 이동
                    parent = parent.parent
                    if not parent or parent.name == 'body':
                        break
            
            # 정당 정보 찾기
            if link.parent:
                party_elem = link.parent.find(class_=re.compile(r'party'))
                if party_elem:
                    party = party_elem.get_text(strip=True)
            
            # 기본값 설정
            if not name:
                name = f"候補者{idx+1}"
            if not party:
                party = "미분류"
            
            return {
                "candidate_id": f"go2s_{candidate_id}",
                "name": name,
                "prefecture": prefecture,
                "constituency": prefecture.replace('都', '').replace('府', '').replace('県', ''),
                "constituency_type": "single_member",
                "party": party,
                "party_normalized": self.normalize_party_name(party),
                "profile_url": profile_url,
                "source_page": page_url,
                "source": "go2senkyo_optimized",
                "collected_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"링크 추출 에러: {e}")
            return None
    
    def extract_candidate_from_block(self, block, prefecture: str, page_url: str, idx: int) -> Optional[Dict[str, Any]]:
        """후보자 블록에서 정보 추출"""
        try:
            # 名前抽出
            name_elem = block.find(class_='p_senkyoku_list_block_text_name')
            full_name = name_elem.get_text(strip=True) if name_elem else f"候補者{idx+1}"
            
            # 名前とカタカナを分離
            name, name_kana = self.separate_name_and_kana(full_name)
            
            # 政党抽出
            party_elem = block.find(class_='p_senkyoku_list_block_text_party')
            party = party_elem.get_text(strip=True) if party_elem else "未分類"
            
            # 프로필 링크 추출
            profile_link = block.find('a', href=re.compile(r'/seijika/\d+'))
            profile_url = ""
            candidate_id = f"{prefecture}_{idx}"
            
            if profile_link:
                href = profile_link.get('href', '')
                if href.startswith('/'):
                    profile_url = urljoin(self.profile_base_url, href)
                else:
                    profile_url = href
                
                # 후보자 ID 추출
                match = re.search(r'/seijika/(\d+)', href)
                if match:
                    candidate_id = f"go2s_{match.group(1)}"
            
            candidate_data = {
                "candidate_id": candidate_id,
                "name": name,
                "prefecture": prefecture,
                "constituency": prefecture.replace('都', '').replace('府', '').replace('県', ''),
                "constituency_type": "single_member",
                "party": party,
                "party_normalized": self.normalize_party_name(party),
                "profile_url": profile_url,
                "source_page": page_url,
                "source": "go2senkyo_optimized",
                "collected_at": datetime.now().isoformat()
            }
            
            # カタカナ名前が存在する場合のみ追加
            if name_kana:
                candidate_data["name_kana"] = name_kana
            
            return candidate_data
            
        except Exception as e:
            logger.debug(f"블록 추출 에러: {e}")
            return None
    
    def normalize_party_name(self, party: str) -> str:
        """정당명 정규화"""
        party_mapping = {
            '自民': '自由民主党', '立憲': '立憲民主党', '維新': '日本維新の会',
            '公明': '公明党', '共産': '日本共産党', '国民': '国民民主党',
            'れいわ': 'れいわ新選組', '社民': '社会民主党', 
            'N国': 'NHK党', '参政': '参政党', '無所属': '無所属'
        }
        
        for key, normalized in party_mapping.items():
            if key in party:
                return normalized
        
        return party if party else "미분류"
    
    def enhance_candidate_profile(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """후보자 프로필 세부 정보 수집"""
        enhanced = candidate.copy()
        profile_url = candidate.get('profile_url', '')
        
        if not profile_url:
            return enhanced
        
        try:
            logger.debug(f"프로필 수집: {candidate.get('name')} - {profile_url}")
            
            self.random_delay(1, 2)
            response = self.session.get(profile_url, timeout=20)
            
            if response.status_code != 200:
                logger.debug(f"프로필 접근 실패: {profile_url}")
                return enhanced
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 프로필 정보 추출
            profile_details = self.extract_profile_details(soup)
            enhanced.update(profile_details)
            
            # 정책 정보 추출
            policy_info = self.extract_policy_info(soup)
            enhanced.update(policy_info)
            
            # 사진 추출
            photo_info = self.extract_photo_info(soup, profile_url)
            enhanced.update(photo_info)
            
            # SNS 링크 추출
            social_info = self.extract_social_links(soup)
            enhanced.update(social_info)
            
            # 통계 업데이트
            self.stats["detailed_profiles"] += 1
            if photo_info.get('photo_url'):
                self.stats["with_photos"] += 1
            if policy_info.get('manifesto_summary'):
                self.stats["with_policies"] += 1
            
        except Exception as e:
            logger.debug(f"프로필 세부정보 에러 ({candidate.get('name')}): {e}")
        
        return enhanced
    
    def extract_profile_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """프로필 세부 정보 추출"""
        details = {}
        
        try:
            # 나이/생년월일
            age_patterns = [
                re.compile(r'(\d{1,2})歳'),
                re.compile(r'([昭平令和]\w*\d+年)'),
                re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日)')
            ]
            
            page_text = soup.get_text()
            for pattern in age_patterns:
                match = pattern.search(page_text)
                if match:
                    details['age_info'] = match.group(1)
                    break
            
            # 경력
            career_keywords = ['経歴', '学歴', 'プロフィール', '略歴']
            for keyword in career_keywords:
                section = soup.find(string=re.compile(keyword))
                if section and section.parent:
                    career_text = section.parent.get_text(strip=True)
                    if len(career_text) > 50:
                        details['career'] = career_text[:500]
                        break
            
            # 직업
            title_keywords = ['職業', '現職', '肩書']
            for keyword in title_keywords:
                section = soup.find(string=re.compile(keyword))
                if section and section.parent:
                    title_text = section.parent.get_text(strip=True)
                    details['occupation'] = title_text[:200]
                    break
        
        except Exception as e:
            logger.debug(f"프로필 상세 추출 에러: {e}")
        
        return details
    
    def extract_policy_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """정책 정보 추출"""
        policy = {}
        
        try:
            policy_keywords = ['政策', 'マニフェスト', '公約', '主張', '取り組み']
            policy_texts = []
            
            for keyword in policy_keywords:
                elements = soup.find_all(string=re.compile(keyword))
                for element in elements:
                    if element.parent:
                        text = element.parent.get_text(strip=True)
                        if len(text) > 30:
                            policy_texts.append(text)
                
                if len(' '.join(policy_texts)) > 300:
                    break
            
            if policy_texts:
                combined = ' '.join(policy_texts)
                sentences = [s.strip() for s in combined.split('。') if s.strip()]
                policy['manifesto_summary'] = '。'.join(sentences[:8])[:800]
        
        except Exception as e:
            logger.debug(f"정책 정보 추출 에러: {e}")
        
        return policy
    
    def extract_photo_info(self, soup: BeautifulSoup, page_url: str) -> Dict[str, Any]:
        """사진 정보 추출"""
        photo = {}
        
        try:
            # 프로필 사진 후보
            img_candidates = soup.find_all('img')
            
            for img in img_candidates:
                alt = img.get('alt', '').lower()
                src = img.get('src', '')
                
                if (any(kw in alt for kw in ['profile', 'candidate', '候補', '写真']) or
                    any(kw in src.lower() for kw in ['profile', 'candidate', '候補'])):
                    
                    if src.startswith('/'):
                        photo_url = urljoin(page_url, src)
                    elif src.startswith('http'):
                        photo_url = src
                    else:
                        continue
                    
                    photo['photo_url'] = photo_url
                    photo['photo_alt'] = img.get('alt', '')
                    break
        
        except Exception as e:
            logger.debug(f"사진 추출 에러: {e}")
        
        return photo
    
    def extract_social_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """SNS 링크 추출"""
        social = {"sns_accounts": {}}
        
        try:
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href'].lower()
                
                if 'twitter.com' in href or 'x.com' in href:
                    social["sns_accounts"]["twitter"] = link['href']
                elif 'facebook.com' in href:
                    social["sns_accounts"]["facebook"] = link['href']
                elif 'instagram.com' in href:
                    social["sns_accounts"]["instagram"] = link['href']
                elif 'youtube.com' in href:
                    social["sns_accounts"]["youtube"] = link['href']
        
        except Exception as e:
            logger.debug(f"SNS 링크 추출 에러: {e}")
        
        return social
    
    def save_optimized_data(self, candidates: List[Dict[str, Any]]):
        """데이터 저장"""
        if not candidates:
            logger.warning("저장할 후보자 데이터가 없습니다")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 파일 경로
        main_file = self.output_dir / f"go2senkyo_optimized_{timestamp}.json"
        latest_file = self.output_dir / "go2senkyo_optimized_latest.json"
        
        # 통계 계산
        party_stats = {}
        pref_stats = {}
        
        for candidate in candidates:
            party = candidate.get('party', '무소속')
            prefecture = candidate.get('prefecture', '미분류')
            
            party_stats[party] = party_stats.get(party, 0) + 1
            pref_stats[prefecture] = pref_stats.get(prefecture, 0) + 1
        
        # 저장 데이터
        save_data = {
            "metadata": {
                "data_type": "go2senkyo_optimized_sangiin_2025",
                "collection_method": "structure_based_scraping",
                "total_candidates": len(candidates),
                "generated_at": datetime.now().isoformat(),
                "source_site": "sangiin.go2senkyo.com + go2senkyo.com",
                "collection_stats": self.stats,
                "quality_metrics": {
                    "detail_coverage": f"{(self.stats['detailed_profiles']/max(len(candidates), 1)*100):.1f}%",
                    "photo_coverage": f"{(self.stats['with_photos']/max(len(candidates), 1)*100):.1f}%",
                    "policy_coverage": f"{(self.stats['with_policies']/max(len(candidates), 1)*100):.1f}%"
                }
            },
            "statistics": {
                "by_party": party_stats,
                "by_prefecture": pref_stats
            },
            "data": candidates
        }
        
        # 파일 저장
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 최적화 데이터 저장 완료:")
        logger.info(f"  - 파일: {main_file}")
        logger.info(f"  - 후보자: {len(candidates)}명")
        logger.info(f"  - 세부정보: {self.stats['detailed_profiles']}명")
        logger.info(f"  - 사진: {self.stats['with_photos']}명")
        logger.info(f"  - 정책: {self.stats['with_policies']}명")

def main():
    """메인 실행"""
    logger.info("🚀 Go2senkyo 최적화 데이터 수집 시작...")
    
    collector = Go2senkyoOptimizedCollector()
    
    try:
        # 주요 도도부현 수집
        candidates = collector.collect_priority_prefectures()
        
        if not candidates:
            logger.error("❌ 후보자 데이터를 수집할 수 없습니다")
            return
        
        # 데이터 저장
        collector.save_optimized_data(candidates)
        
        logger.info("✨ Go2senkyo 최적화 수집 완료")
        
    except KeyboardInterrupt:
        logger.info("⚠️ 사용자 중단")
    except Exception as e:
        logger.error(f"❌ 메인 에러: {e}")
        raise

if __name__ == "__main__":
    main()