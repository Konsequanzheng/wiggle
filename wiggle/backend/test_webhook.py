import argparse
import requests
import sys

# Test URL (only works in n8n editor):
URL = "https://inin.app.n8n.cloud/webhook-test/build-texture"
# Production n8n webhook URL:
# URL = "https://inin.app.n8n.cloud/webhook/build-texture"
# Direct Modal API URL (skip n8n):
# URL = "https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run/build-texture"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--front", required=True, help="path to front image")
    ap.add_argument("--back", required=True, help="path to back image")
    ap.add_argument("--out", default="texture.png", help="output file name")
    args = ap.parse_args()

    files = {
        "front": open(args.front, "rb"),
        "back": open(args.back, "rb"),
    }
    try:
        r = requests.post(URL, files=files, timeout=300)  # 增加到5分钟
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")
        
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {ct}")
        print(f"Response size: {len(r.content)} bytes")
        
        if "image/png" not in ct:
            print("⚠️  Unexpected content-type:", ct, file=sys.stderr)
            if len(r.content) < 1000:
                print("Response body:", r.text[:500], file=sys.stderr)
        
        with open(args.out, "wb") as f:
            f.write(r.content)
        
        if len(r.content) > 0:
            print(f"✓ Saved -> {args.out}")
        else:
            print(f"⚠️  Warning: Empty response saved to {args.out}", file=sys.stderr)
    except Exception as e:
        print("Request failed:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        for f in files.values():
            f.close()

if __name__ == "__main__":
    main()
