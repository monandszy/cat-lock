import os
import urllib.request
import json
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")

def ensure_cat_image() -> str:
    """Downloads a new cat image from The Cat API if it doesn't exist, saves it, and returns the path."""
    if not os.path.exists(PHOTOS_DIR):
        os.makedirs(PHOTOS_DIR)

    api_url = "https://api.thecatapi.com/v1/images/search?limit=100"
    print("Downloading 100 new cat photos from The Cat API...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        headers = { 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        api_key = os.getenv('CAT_API_KEY')
        if api_key:
            print(f"Loaded API key from env (length {len(api_key)})")
            headers['x-api-key'] = api_key
        else:
            print("No API key loaded! Might be restricted to 1 or 10.")
            
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        print(f"Cat API returned {len(data)} items to download.")
            
        last_filepath = ""
        for i, item in enumerate(data):
            image_url = item['url']
            print(f"[{i+1}/{len(data)}] Downloading {image_url}...")
            
            ext = image_url.split('.')[-1]
            if '?' in ext:
                ext = ext.split('?')[0]
            if ext.lower() not in ['jpg', 'jpeg', 'png', 'gif']:
                ext = 'jpg'

            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(PHOTOS_DIR, filename)

            img_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                'Accept': 'image/*'
            }
            img_req = urllib.request.Request(image_url, headers=img_headers)
            try:
                with urllib.request.urlopen(img_req) as img_response, open(filepath, 'wb') as out_file:
                    out_file.write(img_response.read())
                last_filepath = filepath
            except Exception as item_err:
                print(f"Failed to fetch an individual image: {item_err}")
                
        return last_filepath
    except Exception as e:
        print(f"Failed to fetch image: {e}")
        photos = [p for p in os.listdir(PHOTOS_DIR) if os.path.isfile(os.path.join(PHOTOS_DIR, p))]
        if photos:
            return os.path.join(PHOTOS_DIR, photos[0])
        return ""