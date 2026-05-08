import threading
import time
import requests
#keep the app alive by pinging it every 10 minutes
APP_URL = "https://electronic-voting-of-elite.vercel.app/" 
def ping():
    while True:
        try:
            requests.get(APP_URL)
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
        time.sleep(600)  # Ping every 10 minutes

def start_keep_alive():
    t = threading.Thread(target=ping, daemon=True)
    t.start()

if __name__ == "__main__":
    start_keep_alive()
    while True:
        time.sleep(3600)  # Keep the script running
