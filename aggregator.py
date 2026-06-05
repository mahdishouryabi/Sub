#!/usr/bin/env python3
"""
Subscription Aggregator - ترکیب چند subscription در یک فایل
"""

import json
import requests
import sys
from pathlib import Path
from typing import List, Set
from urllib.parse import urlparse

def load_config(config_file: str = "config.json") -> dict:
    """بارگذاری فایل کانفیگ"""
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_subscription(url: str, timeout: int = 10) -> str:
    """دانلود محتوای یک subscription"""
    try:
        print(f"⏳ دانلود از: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        print(f"✅ موفق: {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ خطا در دانلود {url}: {e}")
        return ""

def deduplicate_lines(content: str) -> Set[str]:
    """حذف خطوط تکراری"""
    lines = set()
    for line in content.strip().split('\n'):
        line = line.strip()
        if line:  # خطوط خالی را نادیده بگیر
            lines.add(line)
    return lines

def aggregate_subscriptions(config: dict) -> str:
    """ترکیب تمام subscriptions"""
    all_lines: Set[str] = set()
    
    print(f"\n🔄 شروع دانلود {len(config['subscriptions'])} subscription...")
    print("-" * 50)
    
    for url in config['subscriptions']:
        content = fetch_subscription(url, config.get('timeout', 10))
        unique_lines = deduplicate_lines(content)
        all_lines.update(unique_lines)
        print(f"   ➕ {len(unique_lines)} خط اضافه شد")
    
    print("-" * 50)
    print(f"📊 کل {len(all_lines)} خط منحصربه‌فرد")
    
    # مرتب‌سازی و اتصال
    result = '\n'.join(sorted(all_lines))
    return result

def save_result(content: str, output_file: str) -> None:
    """ذخیره نتیجه"""
    Path(output_file).write_text(content, encoding='utf-8')
    file_size = len(content.encode('utf-8'))
    print(f"✅ ذخیره شد: {output_file}")
    print(f"📦 اندازه فایل: {file_size:,} بایت")

def main():
    """تابع اصلی"""
    try:
        config = load_config()
        print("=" * 50)
        print("🚀 Subscription Aggregator")
        print("=" * 50)
        
        result = aggregate_subscriptions(config)
        save_result(result, config['output_file'])
        
        print("\n✨ تکمیل شد!")
        return 0
    
    except FileNotFoundError:
        print("❌ فایل config.json پیدا نشد!")
        return 1
    except Exception as e:
        print(f"❌ خطا: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
