#!/usr/bin/env python3
"""
名前と読みの分離修正
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_name_separation():
    """名前と読みの分離を修正"""
    logger.info("📝 名前と読みの分離修正開始...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('data', [])
    logger.info(f"📊 対象候補者: {len(candidates)}名")
    
    fixed_count = 0
    
    for candidate in candidates:
        name = candidate.get('name', '')
        original_name = name
        
        # 名前と読みの分離を実行
        new_name, new_kana = separate_name_and_kana_improved(name)
        
        if new_name != name or new_kana:
            # 修正が必要な場合
            candidate['name'] = new_name
            if new_kana:
                candidate['name_kana'] = new_kana
            
            logger.info(f"修正: {original_name} → 名前: {new_name}, 読み: {new_kana}")
            fixed_count += 1
    
    logger.info(f"🎯 修正完了: {fixed_count}名")
    
    # データ保存
    data['metadata']['generated_at'] = datetime.now().isoformat()
    data['metadata']['data_type'] = "go2senkyo_name_fixed_sangiin_2025"
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fixed_file = data_dir / f"go2senkyo_name_fixed_{timestamp}.json"
    
    with open(fixed_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 保存完了: {fixed_file}")

def separate_name_and_kana_improved(full_name):
    """改良された名前とカタカナの分離"""
    
    if not full_name:
        return full_name, ""
    
    # パターン1: 漢字+ひらがな+カタカナ (例: "板津ゆかイタヅユカ")
    pattern1 = re.match(r'^([一-龯]+)([あ-ん]+)([ァ-ヶ]+)$', full_name)
    if pattern1:
        kanji_part = pattern1.group(1)
        hiragana_part = pattern1.group(2)
        katakana_part = pattern1.group(3)
        name = kanji_part + hiragana_part  # "板津ゆか"
        kana = katakana_part  # "イタヅユカ"
        return name, kana
    
    # パターン2: 漢字+カタカナ直結 (例: "森まさこモリマサコ")
    pattern2 = re.match(r'^([一-龯]+[あ-ん]*)([ァ-ヶ]+)$', full_name)
    if pattern2:
        name_part = pattern2.group(1)
        kana_part = pattern2.group(2)
        return name_part, kana_part
    
    # パターン3: カタカナが混在している場合のより詳細な分析
    pattern3 = re.match(r'^([一-龯][一-龯あ-ん]*?)([ァ-ヶ][ァ-ヶ]*?)$', full_name)
    if pattern3:
        name_part = pattern3.group(1)
        kana_part = pattern3.group(2)
        return name_part, kana_part
    
    # パターン4: 全角スペースで区切られている場合
    if '　' in full_name:
        parts = full_name.split('　')
        if len(parts) == 2:
            name_part = parts[0].strip()
            kana_part = parts[1].strip()
            if re.match(r'[ァ-ヶ]+', kana_part):
                return name_part, kana_part
    
    # パターン5: 名前の中にカタカナが含まれているか確認
    if re.search(r'[ァ-ヶ]', full_name):
        # 漢字・ひらがな部分とカタカナ部分を分離
        name_chars = []
        kana_chars = []
        
        for char in full_name:
            if 'ァ' <= char <= 'ヶ':  # カタカナ
                kana_chars.append(char)
            else:  # 漢字・ひらがな
                name_chars.append(char)
        
        if name_chars and kana_chars:
            name = ''.join(name_chars)
            kana = ''.join(kana_chars)
            return name, kana
    
    # 分離できない場合はそのまま返す
    return full_name, ""

def test_name_separation():
    """名前分離のテスト"""
    test_cases = [
        "板津ゆかイタヅユカ",
        "森まさこモリマサコ",
        "はが道也ハガミチヤ", 
        "大内りかオオウチリカ",
        "吉良よし子キラヨシコ",
        "勝部けんじカツベケンジ",
        "田中よしひとタナカヨシヒト",
        "山田太郎",  # カタカナなし
        "田中　タナカ",  # スペース区切り
    ]
    
    logger.info("🧪 名前分離テスト:")
    for test_name in test_cases:
        name, kana = separate_name_and_kana_improved(test_name)
        logger.info(f"  {test_name} → 名前: '{name}', 読み: '{kana}'")

if __name__ == "__main__":
    # まずテストを実行
    test_name_separation()
    
    print("\n" + "="*50)
    
    # 実際の修正を実行
    fix_name_separation()