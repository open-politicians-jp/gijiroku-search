#!/usr/bin/env python3
"""
Smart Skip Functionality for Data Collection

Checks if new data is available before running collection scripts.
Saves execution time and resources by skipping unnecessary collection.
"""

import json
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class UpdateChecker:
    """Check for updates before data collection"""
    
    def __init__(self):
        self.last_update_file = Path(__file__).parent / "data" / "last_updates.json"
        self.last_update_file.parent.mkdir(exist_ok=True)
        
    def load_last_updates(self) -> Dict:
        """Load last update timestamps"""
        try:
            if self.last_update_file.exists():
                with open(self.last_update_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load last updates: {e}")
        
        return {
            "last_updates": {},
            "updated_at": datetime.now().isoformat()
        }
    
    def save_last_updates(self, updates: Dict):
        """Save last update timestamps"""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            with open(self.last_update_file, 'w', encoding='utf-8') as f:
                json.dump(updates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save last updates: {e}")
    
    def check_kokkai_api_latest(self) -> Optional[str]:
        """Check latest date from Kokkai API"""
        try:
            # Get recent speeches to find latest date
            params = {
                'maximumRecords': 1,
                'startRecord': 1,
                'recordPacking': 'json'
            }
            
            response = requests.get(
                "https://kokkai.ndl.go.jp/api/speech",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'speechRecord' in data and data['speechRecord']:
                    # Extract date from first record
                    record = data['speechRecord'][0]
                    if 'date' in record:
                        return record['date']
            
        except Exception as e:
            logger.warning(f"Failed to check Kokkai API: {e}")
        
        return None
    
    def check_committee_sites_latest(self) -> Optional[str]:
        """Check committee websites for latest updates"""
        try:
            # Simple check - we can enhance this later
            sites = [
                "https://www.shugiin.go.jp/internet/itdb_iinkai.nsf/html/iinkai/iin_j0010.htm",
                "https://www.sangiin.go.jp/japanese/joho1/kousei/iinkai/gijiroku/gijiroku.html"
            ]
            
            for site in sites:
                response = requests.head(site, timeout=10)
                if response.status_code == 200:
                    # Check last-modified header
                    last_modified = response.headers.get('last-modified')
                    if last_modified:
                        # Parse and return recent date
                        return datetime.now().strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.warning(f"Failed to check committee sites: {e}")
        
        return None
    
    def should_run_collection(self, data_type: str, force_check: bool = False) -> Tuple[bool, str]:
        """
        Check if data collection should run for given type
        
        Args:
            data_type: Type of data (speeches, questions, bills, committee_news, manifestos)
            force_check: Force collection regardless of last update
            
        Returns:
            Tuple of (should_run, reason)
        """
        if force_check:
            return True, "Force check enabled"
        
        updates = self.load_last_updates()
        last_updates = updates.get("last_updates", {})
        
        # Get last processed date for this data type
        last_processed = last_updates.get(data_type, {}).get("last_processed")
        
        if not last_processed:
            return True, f"No previous {data_type} data found"
        
        # Parse last processed date
        try:
            last_date = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
        except:
            return True, f"Invalid last processed date for {data_type}"
        
        # Check if it's been more than 1 day since last update
        if datetime.now() - last_date > timedelta(days=1):
            return True, f"More than 1 day since last {data_type} update"
        
        # For specific data types, check external sources
        if data_type == "speeches":
            latest_api_date = self.check_kokkai_api_latest()
            if latest_api_date:
                try:
                    api_date = datetime.strptime(latest_api_date, '%Y-%m-%d')
                    if api_date.date() > last_date.date():
                        return True, f"New {data_type} data available (API: {latest_api_date})"
                except:
                    pass
        
        elif data_type == "committee_news":
            latest_site_date = self.check_committee_sites_latest()
            if latest_site_date:
                try:
                    site_date = datetime.strptime(latest_site_date, '%Y-%m-%d')
                    if site_date.date() > last_date.date():
                        return True, f"New {data_type} data available"
                except:
                    pass
        
        elif data_type == "manifestos":
            # Check if it's Monday (weekly collection for manifestos)
            if datetime.now().weekday() == 0:  # Monday
                days_since_last = (datetime.now() - last_date).days
                if days_since_last >= 7:
                    return True, f"Weekly {data_type} collection (Monday)"
        
        # Default: skip collection
        return False, f"No new {data_type} data since {last_processed}"
    
    def update_last_processed(self, data_type: str, items_count: int = 0):
        """Update last processed timestamp for data type"""
        updates = self.load_last_updates()
        
        if "last_updates" not in updates:
            updates["last_updates"] = {}
        
        updates["last_updates"][data_type] = {
            "last_processed": datetime.now().isoformat(),
            "items_processed": items_count,
            "updated_at": datetime.now().isoformat()
        }
        
        self.save_last_updates(updates)
        logger.info(f"Updated last processed for {data_type}: {items_count} items")
    
    def get_skip_summary(self) -> Dict:
        """Get summary of skip status for all data types"""
        data_types = ["speeches", "questions", "bills", "committee_news", "manifestos"]
        summary = {}
        
        for data_type in data_types:
            should_run, reason = self.should_run_collection(data_type)
            summary[data_type] = {
                "should_run": should_run,
                "reason": reason
            }
        
        return summary

def main():
    """CLI interface for update checker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check for data updates")
    parser.add_argument('--data-type', choices=['speeches', 'questions', 'bills', 'committee_news', 'manifestos'], 
                       help='Check specific data type')
    parser.add_argument('--force', action='store_true', help='Force check regardless of last update')
    parser.add_argument('--summary', action='store_true', help='Show summary for all data types')
    
    args = parser.parse_args()
    
    checker = UpdateChecker()
    
    if args.summary:
        summary = checker.get_skip_summary()
        print("\n📊 Data Collection Skip Summary:")
        print("=" * 50)
        
        for data_type, info in summary.items():
            status = "🟢 RUN" if info["should_run"] else "🔴 SKIP"
            print(f"{status} {data_type}: {info['reason']}")
        
        print()
        return
    
    if args.data_type:
        should_run, reason = checker.should_run_collection(args.data_type, args.force)
        
        if should_run:
            print(f"✅ Should collect {args.data_type}: {reason}")
            exit(0)
        else:
            print(f"⏭️ Skip {args.data_type}: {reason}")
            exit(1)
    
    else:
        print("Use --data-type or --summary option")
        exit(1)

if __name__ == "__main__":
    main()