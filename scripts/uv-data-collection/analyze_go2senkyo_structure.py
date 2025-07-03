#!/usr/bin/env python3
"""
Go2senkyo HTML構造分析ツール

東京都ページのHTMLを詳細分析して候補者データの構造を把握する
"""

import requests
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_html_structure():
    """HTML구조 상세 분석"""
    logger.info("🔍 Go2senkyo HTML구조 분석 시작...")
    
    ua = UserAgent()
    session = requests.Session()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
    })
    
    tokyo_url = "https://sangiin.go2senkyo.com/2025/prefecture/13"
    
    try:
        response = session.get(tokyo_url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 모든 클래스명 분석
        logger.info("📋 모든 클래스명 분석...")
        all_classes = set()
        for element in soup.find_all(class_=True):
            if isinstance(element['class'], list):
                all_classes.update(element['class'])
            else:
                all_classes.add(element['class'])
        
        relevant_classes = [cls for cls in all_classes if any(keyword in cls.lower() for keyword in 
                          ['candidate', 'person', 'member', 'card', 'item', 'list', '候補'])]
        
        logger.info(f"🎯 関連クラス数: {len(relevant_classes)}")
        for cls in sorted(relevant_classes)[:20]:
            logger.info(f"  - {cls}")
        
        # 2. 리스트/카드 구조 분석
        logger.info("\n📦 リスト/カード構조 분析...")
        list_containers = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'list|grid|container|wrapper'))
        
        for i, container in enumerate(list_containers[:10]):
            class_name = ' '.join(container.get('class', []))
            children_count = len(container.find_all(['li', 'div', 'article']))
            logger.info(f"  {i+1}: {container.name}.{class_name} - {children_count}개 자식요소")
        
        # 3. 이름이 포함된 요소들 상세 분석
        logger.info("\n👤 이름 포함 요소 분석...")
        name_pattern = re.compile(r'[一-龯]{2,4}[\s　]+[一-龯]{2,8}')
        
        name_elements = []
        for element in soup.find_all(string=name_pattern):
            parent = element.parent if element.parent else None
            if parent:
                name_elements.append({
                    'text': element.strip(),
                    'parent_tag': parent.name,
                    'parent_class': ' '.join(parent.get('class', [])),
                    'parent_id': parent.get('id', ''),
                    'siblings_count': len(parent.find_all())
                })
        
        # 이름 요소의 부모 패턴 분석
        parent_patterns = {}
        for elem in name_elements[:15]:  # 처음 15개만 분석
            pattern = f"{elem['parent_tag']}.{elem['parent_class']}"
            if pattern not in parent_patterns:
                parent_patterns[pattern] = []
            parent_patterns[pattern].append(elem['text'])
        
        logger.info("🏗️ 이름 요소의 부모 패턴:")
        for pattern, names in parent_patterns.items():
            logger.info(f"  {pattern}: {len(names)}개 - {', '.join(names[:3])}...")
        
        # 4. 링크 구조 분석
        logger.info("\n🔗 링크 구조 분석...")
        all_links = soup.find_all('a', href=True)
        
        # 후보자 관련 링크 필터링
        candidate_like_links = []
        for link in all_links:
            href = link['href'].lower()
            text = link.get_text(strip=True)
            
            # 후보자명이나 관련 키워드가 포함된 링크
            if (name_pattern.search(text) or 
                any(keyword in href for keyword in ['candidate', 'person', 'member', 'profile']) or
                any(keyword in text for keyword in ['プロフィール', '候補者', '詳細'])):
                
                candidate_like_links.append({
                    'text': text,
                    'href': href,
                    'parent_class': ' '.join(link.parent.get('class', [])) if link.parent else ''
                })
        
        logger.info(f"🎯 候補者関連リンク: {len(candidate_like_links)}個")
        for i, link in enumerate(candidate_like_links[:10]):
            logger.info(f"  {i+1}: {link['text'][:30]} -> {link['href'][:50]}")
        
        # 5. 이미지 구조 분석
        logger.info("\n🖼️ 이미지 구조 분석...")
        images = soup.find_all('img')
        profile_images = []
        
        for img in images:
            alt = img.get('alt', '').lower()
            src = img.get('src', '').lower()
            
            if (any(keyword in alt for keyword in ['profile', 'candidate', '候補', '写真']) or
                any(keyword in src for keyword in ['profile', 'candidate', '候補', 'photo'])):
                profile_images.append({
                    'alt': img.get('alt', ''),
                    'src': img.get('src', ''),
                    'parent_class': ' '.join(img.parent.get('class', [])) if img.parent else ''
                })
        
        logger.info(f"👤 프로필 이미지 후보: {len(profile_images)}개")
        for i, img in enumerate(profile_images[:5]):
            logger.info(f"  {i+1}: {img['alt'][:30]} - {img['src'][:50]}")
        
        # 6. JavaScript/AJAX 로딩 체크
        logger.info("\n⚡ JavaScript/AJAX 분석...")
        scripts = soup.find_all('script')
        js_patterns = ['ajax', 'fetch', 'candidate', 'person', 'load']
        
        relevant_scripts = []
        for script in scripts:
            if script.string:
                for pattern in js_patterns:
                    if pattern.lower() in script.string.lower():
                        relevant_scripts.append(pattern)
                        break
        
        logger.info(f"🔧 관련 JavaScript 패턴: {set(relevant_scripts)}")
        
        # 7. 최적 선택자 추천
        logger.info("\n🎯 추천 선택자:")
        
        # 가장 많이 등장하는 부모 패턴
        if parent_patterns:
            most_common_pattern = max(parent_patterns.items(), key=lambda x: len(x[1]))
            logger.info(f"  최다 이름 패턴: {most_common_pattern[0]} ({len(most_common_pattern[1])}개)")
        
        # 링크 기반 추천
        if candidate_like_links:
            link_parents = [link['parent_class'] for link in candidate_like_links if link['parent_class']]
            if link_parents:
                from collections import Counter
                common_link_parent = Counter(link_parents).most_common(1)[0]
                logger.info(f"  링크 부모 클래스: .{common_link_parent[0]} ({common_link_parent[1]}개)")
        
        # DOM 구조 기반 추천
        logger.info("  추천 선택자 조합:")
        logger.info("    1. 이름 패턴 + 링크: a[href*='candidate'], a[href*='person']")
        logger.info("    2. 클래스 기반: .candidate-item, .person-card, .member-item")
        logger.info("    3. 구조 기반: ul > li, .grid > div, .list > .item")
        
    except Exception as e:
        logger.error(f"❌ 분석 에러: {e}")

if __name__ == "__main__":
    analyze_html_structure()