# Wiggle Backend

T-shirt texture generation service and testing utilities.

## Architecture

```
Test Script → n8n Webhook → Modal API → Texture Image
```

- **`app.py`**: FastAPI service deployed on Modal (generates 1024x1024 texture)
- **`test_webhook.py`**: Test script for n8n webhook

---

## 1. Deploy Modal API ✅

### Deployed URL
```
https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run/build-texture
```

### Redeploy (if needed)
```bash
uv run modal deploy app.py
```

### View Deployment
https://modal.com/apps/ykzou1214/main/deployed/tshirt-texture-modal

---

## 2. Test Modal API Directly

### Quick Test (without n8n)

**Default (preserve colors/logos)**:
```bash
uv run test_modal_direct.py --front ../../front.png --back ../../back.png
```

**White silhouette mode**:
```bash
uv run test_modal_direct.py --front ../../front.png --back ../../back.png --style silhouette
```

This directly calls the Modal API and saves `texture.png`.

---

## 3. Configure n8n Workflow

In your n8n workflow, update the **"HTTP Request - Build Texture"** node:

- **URL**: `https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run/build-texture`
- **Method**: POST
- **Send Body**: Yes
- **Body Content Type**: Form-Data Multipart
- **Specify Body**: Using Fields
- **Body Parameters**:
  - Name: `front`, Value: `={{ $binary.front }}`
  - Name: `back`, Value: `={{ $binary.back }}`

---

## 4. Test Complete Workflow (n8n → Modal)

### Run Full Pipeline Test

**Test mode (n8n editor)**:
```bash
uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png
```

**Production mode**:
```bash
uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png --production
```

**Custom output filename**:
```bash
uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png --out my_texture.png
```

This will:
1. Send images to your n8n webhook
2. n8n forwards to Modal API  
3. Modal generates texture
4. Returns `texture.png`

### Legacy Test Script
```bash
uv run test_webhook.py --front ../../front.png --back ../../back.png
```

---

## API Details

**Endpoint**: `POST /build-texture`

**Parameters**:
- `front` (file): Front T-shirt image
- `back` (file): Back T-shirt image
- `style` (string, optional): 
  - `"preserve"` (default): Keep colors and logos
  - `"silhouette"`: Pure white silhouette

**Response**: PNG image (1024x1024, black background)

**Features**:
- ✅ Automatic background removal (rembg)
- ✅ Preserves T-shirt colors and designs
- ✅ Converging drape effect (triangles meet at centerline)
- ✅ Vertical motion blur for realistic fabric stretch
- ✅ EXIF orientation correction

---

## Files

- **`app.py`**: Modal FastAPI service (deployed)
- **`test_n8n_workflow.py`**: **New n8n workflow test** (recommended)
- **`test_modal_direct.py`**: Direct Modal API test
- **`test_webhook.py`**: Legacy n8n webhook test
- **`n8n_workflow.json`**: n8n workflow configuration
- **`pyproject.toml`**: Dependencies (requests, modal)
- **`front.png`, `back.png`**: Sample T-shirt images (in parent dir)

---

## Summary

✅ **Modal API deployed**: https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run/build-texture

✅ **Features**:
- Preserves T-shirt colors and logos by default
- Optional white silhouette mode (`?style=silhouette`)
- Converging drape effect (left/right meet at centerline)
- Vertical motion blur for fabric stretch
- Auto background removal with rembg

✅ **Testing**:
```bash
# n8n workflow test (recommended)
uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png

# Direct Modal API test
uv run test_modal_direct.py --front ../../front.png --back ../../back.png

# White silhouette mode
uv run test_modal_direct.py --front ../../front.png --back ../../back.png --style silhouette
```

**n8n workflow**: Import `n8n_workflow.json` into n8n for webhook integration
