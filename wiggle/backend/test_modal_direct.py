import argparse
import requests
import sys

# Direct Modal API endpoint
URL = "https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run/build-texture"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--front", required=True, help="path to front image")
    ap.add_argument("--back", required=True, help="path to back image")
    ap.add_argument("--out", default="texture.png", help="output file name")
    ap.add_argument("--style", default="preserve", choices=["preserve", "silhouette"],
                    help="preserve: keep colors/logos | silhouette: white mask")
    args = ap.parse_args()

    files = {
        "front": open(args.front, "rb"),
        "back": open(args.back, "rb"),
    }
    params = {"style": args.style}
    
    try:
        print(f"Sending request to Modal API (style={args.style})...")
        r = requests.post(URL, files=files, params=params, timeout=120)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")
        if "image/png" not in ct:
            print("Unexpected content-type:", ct, file=sys.stderr)
        with open(args.out, "wb") as f:
            f.write(r.content)
        print(f"✓ Success! Saved -> {args.out}")
    except Exception as e:
        print("Request failed:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        for f in files.values():
            f.close()

if __name__ == "__main__":
    main()
