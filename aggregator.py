#!/usr/bin/env python3
"""
Subscription Aggregator - ترکیب چند subscription در یک فایل
"""

import json
import requests
import sys
from pathlib import Path
from typing import List, Set, Optional
from urllib.parse import urlparse, unquote
import base64
import json

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

def safe_b64_decode(s: str) -> bytes:
    s = s.strip()
    missing = len(s) % 4
    if missing:
        s += '=' * (4 - missing)
    return base64.urlsafe_b64decode(s)


def extract_name(line: str) -> Optional[str]:
    """Extract a human-readable name from known subscription formats.

    Returns None if no name could be determined.
    """
    try:
        if line.startswith('vmess://'):
            b = line[len('vmess://'):]
            try:
                decoded = safe_b64_decode(b).decode('utf-8')
                obj = json.loads(decoded)
                return obj.get('ps') or obj.get('name')
            except Exception:
                return None

        if line.startswith('trojan://'):
            p = urlparse(line)
            if p.fragment:
                return unquote(p.fragment)
            # fallback to host
            return p.hostname

        if line.startswith('ss://'):
            # ss://...#name or ss://base64#name
            if '#' in line:
                return unquote(line.split('#', 1)[1])
            # attempt to decode base64 payload
            body = line[len('ss://'):]
            parts = body.split('#', 1)
            b64 = parts[0]
            try:
                decoded = safe_b64_decode(b64).decode('utf-8')
                # method:password@host:port
                if '@' in decoded:
                    right = decoded.split('@', 1)[1]
                    host = right.split(':', 1)[0]
                    return host
            except Exception:
                return None

    except Exception:
        return None
    return None


def deduplicate_lines(content: str) -> Set[str]:
    """حذف خطوط تکراری (exact) - بازگرداندن مجموعه خطوط یکتا"""
    lines = set()
    for line in content.strip().split('\n'):
        line = line.strip()
        if line:
            lines.add(line)
    return lines

def aggregate_subscriptions(config: dict) -> str:
    """ترکیب تمام subscriptions و حذف موارد تکراری بر اساس محتوا و نام"""
    all_lines: Set[str] = set()

    print(f"\n🔄 شروع دانلود {len(config['subscriptions'])} subscription...")
    print("-" * 50)

    # پردازش به صورت ترتیبی بر اساس ترتیب URL‌ها؛ اگر نام یکسان دیده شد، مورد جدید جایگزین قبلی می‌شود
    seen_exact = set()
    name_to_line = {}
    no_name_lines = []

    for url in config['subscriptions']:
        content = fetch_subscription(url, config.get('timeout', 10))
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        print(f"   ➕ {len(lines)} خط از {url}")
        for line in lines:
            if line in seen_exact:
                continue
            seen_exact.add(line)
            name = extract_name(line)
            if name:
                # اگر قبلاً نام دیده شده، حذف و دوباره درج می‌کنیم تا ترتیبِ جدید حفظ شود
                if name in name_to_line:
                    try:
                        del name_to_line[name]
                    except KeyError:
                        pass
                name_to_line[name] = line
            else:
                # خطوط بدون نام را نگه می‌داریم (تک‌رشته‌ای)
                no_name_lines.append(line)

    # ترکیب خروجی: ابتدا خطوط بدون نام (مرتب‌شده)، سپس خطوط با نام به‌ترتیب آخرین وقوع
    final_lines = sorted(no_name_lines) + list(name_to_line.values())
    print(f"-" * 50)
    print(f"📊 پس از حذف تکراری‌ها و هم‌نام‌ها: {len(final_lines)} خط باقی ماند")

    result = '\n'.join(final_lines)
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
