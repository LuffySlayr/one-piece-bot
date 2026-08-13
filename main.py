import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# משיכת מפתחות הטלגרם ממשתני הסביבה שנגדיר בענן
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

seen_products = set()

def send_telegram_alert(site_name, title, link, price="N/A"):
    """שליחת התראה לטלגרם"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("חסר Token או Chat ID בטלגרם")
        return

    message = (
        f"🚨 <b>מלאי/Pre-Order חדש לוואן פיס!</b>\n\n"
        f"🏠 <b>חנות:</b> {site_name}\n"
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"שגיאה בשליחת הודעה לטלגרם: {e}")

def check_shopify_store(site_name, domain):
    """בדיקת חנויות במקביל בגישת JSON API"""
    try:
        url = f"https://{domain}/products.json?limit=30"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for product in data.get("products", []):
                title = product.get("title", "")
                title_lower = title.lower()
                
                # סינון לפי מילות מפתח
                if "one piece" in title_lower or "op-" in title_lower or "eb-" in title_lower:
                    product_id = f"{site_name}_{product['id']}"
                    
                    if product_id not in seen_products:
                        variants = product.get("variants", [])
                        available = any(v.get("available", False) for v in variants)
                        
                        if available:
                            price = f"£{variants[0].get('price')}" if variants else "N/A"
                            handle = product.get("handle", "")
                            prod_url = f"https://{domain}/products/{handle}"
                            
                            seen_products.add(product_id)
                            send_telegram_alert(site_name, title, prod_url, price)
    except Exception as e:
        print(f"שגיאה בסריקת {site_name}: {e}")

def check_all_stores():
    """הרצת סריקה על ארבעת האתרים"""
    check_shopify_store("Total Cards", "www.totalcards.net")
    check_shopify_store("Zatu Games", "www.board-game.co.uk")
    check_shopify_store("Chaos Cards", "www.chaoscards.co.uk")
    check_shopify_store("The Card Garden", "thecardgarden.com")

def monitor_loop():
    send_telegram_alert("בדיקת מערכת", "הבוט מחובר, סורק ועובד מעולה!", "https://one-piece-bot-ggjd.onrender.com", "0")
    """לולאת בדיקה כל 60 שניות"""
    print("🤖 הבוט התחיל לנטר את האתרים...")
    while True:
        try:
            check_all_stores()
        except Exception as e:
            print(f"שגיאה בלולאת הניטור: {e}")
        time.sleep(60)

@app.route('/')
def home():
    return "One Piece Bot is Active and Running!"

if __name__ == '__main__':
    # הפעלת סריקת הרקע
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    
    # הרצת שרת ה-Web
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
