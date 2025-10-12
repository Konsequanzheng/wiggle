#!/usr/bin/env python3
"""
Test script for n8n workflow: Build T-shirt Texture

Workflow flow:
1. Webhook In (POST /build-texture) - receives front/back images
2. Pass Through - passes data
3. HTTP Request - Build Texture - calls Modal API with multipart form data
4. Rename Binary → texture - renames response binary
5. Respond to Webhook - returns texture.png with proper headers

Usage:
    # Test mode (n8n editor):
    uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png
    
    # Production mode:
    uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png --production
    
    # Custom webhook URL:
    uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png --url YOUR_WEBHOOK_URL
    
    # Custom output:
    uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png --out output.png
"""

import argparse
import requests
import sys
import os
from pathlib import Path

# n8n webhook endpoints
TEST_URL = "https://inin.app.n8n.cloud/webhook-test/build-texture"
PROD_URL = "https://inin.app.n8n.cloud/webhook/build-texture"

def validate_file(file_path: str) -> bool:
    """Validate that file exists and is readable"""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}", file=sys.stderr)
        return False
    if not os.path.isfile(file_path):
        print(f"❌ Error: Not a file: {file_path}", file=sys.stderr)
        return False
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Test n8n workflow for T-shirt texture generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test in n8n editor (default)
  %(prog)s --front ../../front.png --back ../../back.png
  
  # Test production webhook
  %(prog)s --front ../../front.png --back ../../back.png --production
  
  # Use custom webhook URL
  %(prog)s --front ../../front.png --back ../../back.png --url YOUR_WEBHOOK_URL
  
  # Save with custom filename
  %(prog)s --front ../../front.png --back ../../back.png --out my_texture.png
        """
    )
    
    parser.add_argument(
        "--front",
        required=True,
        help="Path to front T-shirt image"
    )
    parser.add_argument(
        "--back",
        required=True,
        help="Path to back T-shirt image"
    )
    parser.add_argument(
        "--out",
        default="texture.png",
        help="Output filename (default: texture.png)"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use production webhook URL (default: test URL)"
    )
    parser.add_argument(
        "--url",
        help="Custom webhook URL (overrides --production)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Request timeout in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    # Validate input files
    if not validate_file(args.front):
        sys.exit(1)
    if not validate_file(args.back):
        sys.exit(1)
    
    # Select URL
    if args.url:
        url = args.url
        mode = "CUSTOM"
    elif args.production:
        url = PROD_URL
        mode = "PRODUCTION"
    else:
        url = TEST_URL
        mode = "TEST"
    
    print(f"🔧 Mode: {mode}")
    print(f"📡 URL: {url}")
    print(f"📸 Front: {args.front}")
    print(f"📸 Back: {args.back}")
    print(f"⏱️  Timeout: {args.timeout}s")
    print()
    
    # Prepare multipart form data
    files = {
        "front": (Path(args.front).name, open(args.front, "rb"), "image/png"),
        "back": (Path(args.back).name, open(args.back, "rb"), "image/png"),
    }
    
    try:
        print("🚀 Sending request to n8n webhook...")
        response = requests.post(url, files=files, timeout=args.timeout)
        
        # Check response status
        print(f"📊 Status Code: {response.status_code}")
        
        # Raise error for bad status codes
        response.raise_for_status()
        
        # Check response headers
        content_type = response.headers.get("Content-Type", "")
        content_length = len(response.content)
        content_disposition = response.headers.get("Content-Disposition", "")
        
        print(f"📋 Content-Type: {content_type}")
        print(f"📦 Content-Length: {content_length:,} bytes")
        if content_disposition:
            print(f"📎 Content-Disposition: {content_disposition}")
        print()
        
        # Validate content type
        if "image/png" not in content_type:
            print(f"⚠️  Warning: Unexpected Content-Type: {content_type}", file=sys.stderr)
            print(f"    Expected: image/png", file=sys.stderr)
            if content_length < 1000:
                print(f"📄 Response preview: {response.text[:500]}", file=sys.stderr)
            print()
        
        # Check if response is empty
        if content_length == 0:
            print(f"❌ Error: Empty response received", file=sys.stderr)
            sys.exit(1)
        
        # Save response to file
        with open(args.out, "wb") as f:
            f.write(response.content)
        
        # Success message
        print(f"✅ Success! Texture saved to: {args.out}")
        print(f"📏 File size: {content_length:,} bytes")
        
        # Verify saved file
        if os.path.exists(args.out):
            saved_size = os.path.getsize(args.out)
            if saved_size == content_length:
                print(f"✓ File verification passed")
            else:
                print(f"⚠️  Warning: Size mismatch - saved:{saved_size} vs received:{content_length}", file=sys.stderr)
        
    except requests.exceptions.Timeout:
        print(f"❌ Error: Request timeout after {args.timeout}s", file=sys.stderr)
        print(f"   Try increasing timeout with --timeout option", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error: Connection failed", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error: HTTP {response.status_code}", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        if response.text:
            print(f"📄 Response: {response.text[:500]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Close file handles
        for file_tuple in files.values():
            if hasattr(file_tuple[1], 'close'):
                file_tuple[1].close()

if __name__ == "__main__":
    main()
