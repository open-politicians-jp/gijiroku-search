#!/usr/bin/env python3
"""
HTML構造デバッグ - NHK・朝日新聞のページ構造を分析
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path

def analyze_nhk_structure():
    """NHKページの構造分析"""
    print("🔍 NHKページ構造分析開始...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,ja-JP;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.co.jp/',
    })
    
    try:
        url = "https://www.nhk.or.jp/senkyo/database/sangiin/2025/expected-candidates/"
        response = session.get(url, timeout=30)
        
        print(f"ステータス: {response.status_code}")
        print(f"コンテンツ長: {len(response.text):,} 文字")
        
        # HTMLファイルとして保存
        debug_dir = Path(__file__).parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        
        with open(debug_dir / "nhk_page.html", 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 都道府県関連のテキストを含む要素を探す
        print("\n📋 都道府県関連要素:")
        prefecture_keywords = ['都道府県', '選挙区', '地域', '候補者', '北海道', '東京都', '神奈川県', '京都府']
        
        for keyword in prefecture_keywords:
            elements = soup.find_all(string=re.compile(keyword))
            print(f"  {keyword}: {len(elements)}件")
            if elements:
                for elem in elements[:3]:  # 最初の3件
                    parent = elem.parent if elem.parent else None
                    print(f"    - {elem.strip()[:50]}... (親: {parent.name if parent else 'None'})")
        
        # すべてのリンクを確認
        print("\n🔗 全リンク分析:")
        links = soup.find_all('a', href=True)
        print(f"  総リンク数: {len(links)}")
        
        prefecture_links = []
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 都道府県関連のリンクを探す
            if any(keyword in text for keyword in ['県', '都', '府', '道', '選挙区']):
                prefecture_links.append((text, href))
        
        print(f"  都道府県関連リンク: {len(prefecture_links)}件")
        for text, href in prefecture_links[:10]:  # 最初の10件
            print(f"    - {text} → {href}")
        
        # JavaScriptで動的に生成される可能性をチェック
        scripts = soup.find_all('script')
        print(f"\n📜 JavaScript: {len(scripts)}件")
        
        for script in scripts:
            script_content = script.string if script.string else ""
            if any(keyword in script_content for keyword in ['prefecture', '都道府県', 'candidate']):
                print(f"  関連スクリプト発見: {script_content[:100]}...")
        
        return response.text
        
    except Exception as e:
        print(f"❌ NHK分析エラー: {e}")
        return None

def analyze_asahi_structure():
    """朝日新聞ページの構造分析"""
    print("\n🔍 朝日新聞ページ構造分析開始...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,ja-JP;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.co.jp/',
    })
    
    try:
        url = "https://www.asahi.com/senkyo/saninsen/koho/"
        response = session.get(url, timeout=30)
        
        print(f"ステータス: {response.status_code}")
        print(f"コンテンツ長: {len(response.text):,} 文字")
        
        # HTMLファイルとして保存
        debug_dir = Path(__file__).parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        
        with open(debug_dir / "asahi_page.html", 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 都道府県関連のテキストを含む要素を探す
        print("\n📋 都道府県関連要素:")
        prefecture_keywords = ['都道府県', '選挙区', '地域', '候補者', '北海道', '東京都', '神奈川県', '京都府']
        
        for keyword in prefecture_keywords:
            elements = soup.find_all(string=re.compile(keyword))
            print(f"  {keyword}: {len(elements)}件")
            if elements:
                for elem in elements[:3]:  # 最初の3件
                    parent = elem.parent if elem.parent else None
                    print(f"    - {elem.strip()[:50]}... (親: {parent.name if parent else 'None'})")
        
        # すべてのリンクを確認
        print("\n🔗 全リンク分析:")
        links = soup.find_all('a', href=True)
        print(f"  総リンク数: {len(links)}")
        
        prefecture_links = []
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 都道府県関連のリンクを探す
            if any(keyword in text for keyword in ['県', '都', '府', '道', '選挙区']):
                prefecture_links.append((text, href))
        
        print(f"  都道府県関連リンク: {len(prefecture_links)}件")
        for text, href in prefecture_links[:10]:  # 最初の10件
            print(f"    - {text} → {href}")
        
        # select要素やoption要素をチェック
        selects = soup.find_all('select')
        print(f"\n📋 セレクトボックス: {len(selects)}件")
        
        for select in selects:
            options = select.find_all('option')
            print(f"  セレクト: {len(options)}個のオプション")
            for option in options[:5]:  # 最初の5件
                print(f"    - {option.get_text(strip=True)} (value: {option.get('value', '')})")
        
        return response.text
        
    except Exception as e:
        print(f"❌ 朝日新聞分析エラー: {e}")
        return None

def main():
    """メイン処理"""
    print("🔍 HTML構造デバッグ開始...")
    
    # NHK分析
    nhk_content = analyze_nhk_structure()
    
    # 朝日新聞分析
    asahi_content = analyze_asahi_structure()
    
    print("\n✅ HTML構造分析完了")
    print("📁 デバッグファイルは debug/ ディレクトリに保存されました")

if __name__ == "__main__":
    main()