#!/usr/bin/env python3
"""
データ増加状況確認スクリプト

各データタイプの最終更新日と件数を確認し、データが増加していない理由を分析
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataGrowthChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "frontend" / "public" / "data"
        
    def check_all_data_types(self):
        """全データタイプの成長状況をチェック"""
        logger.info("📊 データ成長状況チェック開始...")
        
        data_types = {
            "speeches": "議事録",
            "questions": "質問主意書", 
            "bills": "提出法案",
            "committee_news": "委員会ニュース",
            "manifestos": "マニフェスト"
        }
        
        results = {}
        
        for data_type, display_name in data_types.items():
            logger.info(f"\n🔍 {display_name}データチェック...")
            result = self.check_data_type(data_type)
            results[data_type] = result
            self.display_result(display_name, result)
        
        # 総合サマリー
        self.display_summary(results)
        
        return results
    
    def check_data_type(self, data_type: str) -> Dict[str, Any]:
        """特定データタイプの成長状況をチェック"""
        data_type_dir = self.data_dir / data_type
        
        if not data_type_dir.exists():
            return {
                "status": "missing",
                "message": "ディレクトリが存在しません",
                "files": [],
                "latest_file": None,
                "total_records": 0,
                "last_update": None
            }
        
        # ファイル一覧取得
        json_files = list(data_type_dir.glob("*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not json_files:
            return {
                "status": "empty",
                "message": "JSONファイルが存在しません",
                "files": [],
                "latest_file": None,
                "total_records": 0,
                "last_update": None
            }
        
        # 最新ファイル分析
        latest_file = json_files[0]
        latest_analysis = self.analyze_file(latest_file)
        
        # 全ファイル分析
        file_analysis = []
        for file_path in json_files[:10]:  # 最新10ファイルのみ
            analysis = self.analyze_file(file_path)
            file_analysis.append(analysis)
        
        # 更新パターン分析
        update_pattern = self.analyze_update_pattern(file_analysis)
        
        return {
            "status": "active" if latest_analysis["records"] > 0 else "inactive",
            "files": file_analysis,
            "latest_file": latest_analysis,
            "total_files": len(json_files),
            "update_pattern": update_pattern,
            "last_update": latest_analysis["last_modified"],
            "total_records": latest_analysis["records"]
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """個別ファイル分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # ファイルサイズ
            file_size = file_path.stat().st_size
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # レコード数の取得
            records = 0
            data_structure = "unknown"
            
            if isinstance(data, list):
                records = len(data)
                data_structure = "array"
            elif isinstance(data, dict):
                if "data" in data and isinstance(data["data"], list):
                    records = len(data["data"])
                    data_structure = "object_with_data"
                elif "statistics" in data:
                    data_structure = "statistics"
                else:
                    data_structure = "object"
            
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "last_modified": last_modified,
                "last_modified_str": last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                "records": records,
                "data_structure": data_structure,
                "days_old": (datetime.now() - last_modified).days
            }
            
        except Exception as e:
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "error": str(e),
                "records": 0,
                "last_modified": None
            }
    
    def analyze_update_pattern(self, file_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新パターンの分析"""
        if not file_analysis:
            return {"pattern": "no_data"}
        
        # 最新3ファイルの比較
        recent_files = file_analysis[:3]
        record_counts = [f["records"] for f in recent_files if "records" in f]
        
        if len(record_counts) < 2:
            return {"pattern": "insufficient_data"}
        
        # レコード数の変化
        if all(count == record_counts[0] for count in record_counts):
            pattern = "static"  # 変化なし
        elif record_counts[0] > record_counts[1]:
            pattern = "growing"  # 増加
        else:
            pattern = "decreasing"  # 減少
        
        # 更新頻度
        dates = [f["last_modified"] for f in recent_files if f["last_modified"]]
        if len(dates) >= 2:
            time_diff = (dates[0] - dates[1]).days
            if time_diff <= 1:
                frequency = "daily"
            elif time_diff <= 7:
                frequency = "weekly"
            else:
                frequency = "irregular"
        else:
            frequency = "unknown"
        
        return {
            "pattern": pattern,
            "frequency": frequency,
            "record_counts": record_counts,
            "latest_count": record_counts[0] if record_counts else 0
        }
    
    def display_result(self, data_name: str, result: Dict[str, Any]):
        """結果表示"""
        status = result["status"]
        
        if status == "missing":
            logger.warning(f"❌ {data_name}: ディレクトリなし")
        elif status == "empty":
            logger.warning(f"📂 {data_name}: ファイルなし")
        elif status == "inactive":
            logger.warning(f"⚠️ {data_name}: データなし")
        else:
            latest = result["latest_file"]
            pattern = result["update_pattern"]
            
            logger.info(f"✅ {data_name}:")
            logger.info(f"  📁 ファイル数: {result['total_files']}")
            logger.info(f"  📄 最新ファイル: {latest['file_name']}")
            logger.info(f"  📊 レコード数: {latest['records']:,}")
            logger.info(f"  📅 最終更新: {latest['last_modified_str']} ({latest['days_old']}日前)")
            logger.info(f"  💾 ファイルサイズ: {latest['file_size_mb']}MB")
            logger.info(f"  📈 更新パターン: {pattern['pattern']} ({pattern['frequency']})")
    
    def display_summary(self, results: Dict[str, Any]):
        """総合サマリー表示"""
        logger.info("\n" + "="*60)
        logger.info("📋 データ成長状況サマリー")
        logger.info("="*60)
        
        active_data = []
        inactive_data = []
        
        for data_type, result in results.items():
            if result["status"] == "active":
                latest = result["latest_file"]
                days_old = latest["days_old"]
                records = latest["records"]
                pattern = result["update_pattern"]["pattern"]
                
                active_data.append({
                    "type": data_type,
                    "days_old": days_old,
                    "records": records,
                    "pattern": pattern
                })
            else:
                inactive_data.append({
                    "type": data_type,
                    "status": result["status"]
                })
        
        # アクティブなデータ
        if active_data:
            logger.info("\n✅ アクティブなデータ:")
            for data in sorted(active_data, key=lambda x: x["days_old"]):
                logger.info(f"  {data['type']}: {data['records']:,}件 ({data['days_old']}日前, {data['pattern']})")
        
        # 問題のあるデータ
        if inactive_data:
            logger.info("\n⚠️ 問題のあるデータ:")
            for data in inactive_data:
                logger.info(f"  {data['type']}: {data['status']}")
        
        # 推奨アクション
        logger.info("\n💡 推奨アクション:")
        old_data = [d for d in active_data if d["days_old"] > 7]
        static_data = [d for d in active_data if d["pattern"] == "static"]
        
        if old_data:
            logger.info("  📅 1週間以上更新されていないデータの収集を実行")
            for data in old_data:
                logger.info(f"    - {data['type']}")
        
        if static_data:
            logger.info("  🔄 レコード数が変化していないデータの収集方法を見直し")
            for data in static_data:
                logger.info(f"    - {data['type']}")
        
        if inactive_data:
            logger.info("  ❌ データ収集が停止しているものを再開")
            for data in inactive_data:
                logger.info(f"    - {data['type']}")

def main():
    """メイン実行"""
    checker = DataGrowthChecker()
    results = checker.check_all_data_types()
    
    # 結果をJSONで出力（GitHub Actionsでの利用想定）
    output_file = Path(__file__).parent / "data_growth_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "results": results
        }, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"\n📄 詳細レポート保存: {output_file}")

if __name__ == "__main__":
    main()