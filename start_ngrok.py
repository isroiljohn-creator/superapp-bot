from pyngrok import ngrok
import time

# Open a HTTP tunnel on the default port 8000
public_url = ngrok.connect(8000).public_url
print(f"NGROK_URL={public_url}")

# Keep it alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping ngrok...")
