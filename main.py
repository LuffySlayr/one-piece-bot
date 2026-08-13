import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# דף הבית כדי לוודא שהשרת חי (בריאות השרת עבור UptimeRobot)
@app.route('/')
def home():
    return "One Piece Bot is Active and Running!", 200

# משתני סביבה לחיבור לטלגרם
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

seen_products = set()

def send_telegram_alert(site_name, title, link, price="N/A"):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ חסר TELEGRAM_TOKEN או TELEGRAM_CHAT_ID במשתני הסביבה")
        return

    message = (
        f"🚨 <b>Pre-Order / חזור למלאי חדש!</b>\n\n"
        f"🏪 <b>חנות:</b> {site_name}\n"
        f"📦 <b>מוצר:</b> {title}\n"
        f"💰 <b>מחיר:</b> {price}\n\n"
        f"🔗 <a href='{link}'>לחץ כאן למעבר מהיר למוצר</a>"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ התראה נשלחה בהצלחה לטלגרם עבור: {title}")
        else:
            print(f"⚠️ שגיאה בשליחה לטלגרם: {response.text}")
    except Exception as e:
        print(f"❌ שגיאה בשליחת הודעה לטלגרם: {e}")

def check_shopify_store(site_name, domain):
    try:
        url = f"https://{domain}/products.json?limit=30"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            for product in data.get("products", []):
                title = product.get("title", "")
                title_lower = title.lower()

                # סינון לפי מילות מפתח של וואן פיס
                if "one piece" in title_lower or "op-" in title_lower or "eb-" in title_lower or "op0" in title_lower or "op1" in title_lower:
                    product_id = f"{site_name}_{product['id']}"

                    # בדיקת זמינות במלאי
                    variants = product.get("variants", [])
                    available = any(v.get("available", False) for v in variants)
                    
                    price = variants[0].get("price", "N/A") if variants else "N/A"
                    if price != "N/A":
                        price = f"{price} ₪"

                    handle = product.get("handle", "")
                    link = f"https://{domain}/products/{handle}"

                    # אם המוצר זמין במלאי ועוד לא ראינו אותו
                    if available and product_id not in seen_products:
                        seen_products.add(product_id)
                        send_telegram_alert(site_name, title, link, price)
                    elif not available:
                        # במידה ויצא מהמלאי, מסירים מהזיכרון כדי להתריע כשיחזור
                        seen_products.discard(product_id)
    except Exception as e:
        print(f"❌ שגיאה בסריקת האתר {site_name}: {e}")

# רשימת האתרים לסריקה
STORES = [
    {"name": "Comics & Vegetable", "domain": "cnv.co.il"},
    {"name": "Freak", "domain": "freak.org.il"},
    {"name": "Kingdoms", "domain": "kingdoms.co.il"},
    {"name": "PC Games", "domain": "pcgames.co.il"}
]

def monitor_loop():
    print("🤖 הבוט התחיל לנטר את האתרים...")
    
    # שליחת הודעת בדיקה ישר בעליית השרת
    send_telegram_alert("בדיקת מערכת", "הבוט מחובר, פועל ומנטר את האתרים בהצלחה! 🔥", "https://one-piece-bot-ggjd.onrender.com", "0")

    while True:
        for store in STORES:
            check_shopify_store(store["name"], store["domain"])
            time.sleep(2)
        
        time.sleep(60) # הרצה בדיקת סריקה כל 60 שניות

# הפעלת תהליך הניטור ברקע באופן אוטומטי בטעינת הקובץ (מטפל ב-Gunicorn)
threading.Thread(target=monitor_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
