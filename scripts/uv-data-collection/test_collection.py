#!/usr/bin/env python3
"""
データ収集システムのテストスクリプト
2025年1月の数日分だけを取得してシステム動作を確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_2025_all_data import AdvancedKokkaiAPIClient
import logging

# ログレベルを調整
logging.getLogger().setLevel(logging.INFO)

def test_collection():
    """テスト収集実行"""
    print("🧪 データ収集システムテスト開始")
    print("=" * 40)
    
    client = AdvancedKokkaiAPIClient(use_proxy_rotation=False)
    
    try:
        # 2025年1月1-3日のデータを少量取得
        test_data = client.fetch_speeches(
            from_date="2025-01-01",
            until_date="2025-01-03", 
            start_record=1,
            max_records=10
        )
        
        print(f"✅ APIテスト成功")
        print(f"📊 取得レコード数: {len(test_data.get('speechRecord', []))}")
        
        if 'speechRecord' in test_data and test_data['speechRecord']:
            sample = test_data['speechRecord'][0]
            print(f"📝 サンプルデータ:")
            print(f"  日付: {sample.get('date')}")
            print(f"  発言者: {sample.get('speaker')}")
            print(f"  政党: {sample.get('speakerGroup')}")
            print(f"  院: {sample.get('nameOfHouse')}")
        
        print(f"\n🎯 IP偽装機能テスト:")
        print(f"  User-Agent: {client.session.headers.get('User-Agent', 'N/A')[:80]}...")
        print(f"  リクエスト回数: {client.request_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        return False
    
    finally:
        client.cleanup()

if __name__ == "__main__":
    success = test_collection()
    if success:
        print(f"\n✅ テスト完了！本格収集の準備ができています。")
        print(f"🚀 本格収集を開始するには:")
        print(f"   uv run fetch_2025_all_data.py")
    else:
        print(f"\n❌ テスト失敗。設定を確認してください。")
    
    sys.exit(0 if success else 1)