# 🔗 Subscription Aggregator

ترکیب و یکی‌سازی چند subscription URL در یک فایل واحد

## ✨ ویژگی‌ها

- ✅ دانلود خودکار از چند URL
- ✅ حذف خطوط تکراری
- ✅ مرتب‌سازی نتایج
- ✅ اجرای خودکار هر 6 ساعت
- ✅ ذخیره روی GitHub

## 📦 نصب

```bash
# نیازمندی‌ها
pip install requests
```

## 🔧 راهنمای استفاده

### 1️⃣ تنظیم کانفیگ

فایل `config.json` را ویرایش کنید و URLs را اضافه کنید:

```json
{
  "subscriptions": [
    "https://example.com/sub1.txt",
    "https://example.com/sub2.txt",
    "https://example.com/sub3.txt"
  ],
  "output_file": "merged_subscription.txt",
  "timeout": 10
}
```

### 2️⃣ اجرای دستی

```bash
python aggregator.py
```

نتیجه در فایل `merged_subscription.txt` ذخیره می‌شود.

### 3️⃣ اجرای خودکار

Workflow در `.github/workflows/update-subscription.yml` اتوماتیک:
- هر 6 ساعت یکبار اجرا می‌شود
- یا می‌توانید دستی از Actions فعال کنید

## 📊 مثال

**ورودی:**
```
https://example.com/sub1.txt  →  line1, line2, line3
https://example.com/sub2.txt  →  line2, line4
```

**خروجی:**
```
line1
line2
line3
line4
```

## 🔐 نکات ایمنی

- توصیه می‌شود subscription URLs معتبر و ایمن باشند
- فایل تولیدشده فقط‌خواندنی است
- محتوا قبل از استفاده بررسی شود

## 📝 لایسنس

MIT
