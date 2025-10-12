# app.py  —— Modal + FastAPI：/build-texture
# 默认 style=preserve（保留颜色与图案）；如需白衣蒙版，用 style=silhouette

from modal import Image as ModalImage, App, asgi_app

# ---- Modal 运行环境 ----
app = App("tshirt-texture-modal")

modal_image = (
    ModalImage.debian_slim()
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install(
        "fastapi==0.115.0",
        "uvicorn==0.30.6",
        "python-multipart==0.0.9",
        "pillow==10.4.0",
        "numpy==2.1.1",
        "scipy==1.13.1",
        "rembg==2.0.56",
    )
)

@app.function(image=modal_image)
@asgi_app()
def _asgi_app():
    from fastapi import FastAPI, File, UploadFile, Response, HTTPException, Query
    from io import BytesIO
    import numpy as np
    from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageChops
    
    # ---- 版式参数 ----
    SIZE = 1024
    PAD = round(SIZE * 0.06)
    cellW = (SIZE - PAD * 3) // 2
    cellH = (SIZE - PAD * 3) // 2

    # ---- 可调参数的默认值 ----
    APEX_X_RATIO_DEFAULT = 0.50      # 顶点在画布中线
    APEX_Y_RATIO_DEFAULT = 0.965     # 顶点更靠下
    CENTER_BASE_EXPAND_DEFAULT = 0.35 # 中央三角底边向两侧外扩(按 cellW 比例)
    CENTER_TOP_OFFSET_DEFAULT = -0.04 # 中央三角的底边相对下排顶边的位移(负数=上移)
    CENTER_FADE_POWER_DEFAULT = 1.0   # 渐隐强度(越小越"饱满")
    CENTER_STREAK_DEFAULT = 14        # 竖向拉丝
    CENTER_BLUR_DEFAULT = 1.2         # 柔化
    CENTER_INTENSITY_DEFAULT = 0.95   # preserve模式下的高光强度
    OVERLAP_PX_DEFAULT = 10           # 与左右下摆重叠像素（防止黑缝）
    FADE_POWER = 1.0                  # 左右下摆自身的渐隐强度

    # ---- 工具函数 ----
    def load_and_orient(b: bytes):
        im = Image.open(BytesIO(b)).convert("RGBA")
        return ImageOps.exif_transpose(im)

    def remove_bg(im_rgba):
        """rembg 抠图，返回 RGBA，alpha 表示前景"""
        from rembg import remove
        out = remove(np.array(im_rgba))
        return Image.fromarray(out, mode="RGBA")

    def largest_component_from_alpha(a_img, min_keep=0.02):
        """保留 alpha mask 最大连通域，去掉零碎背景"""
        from scipy import ndimage as ndi
        a = np.array(a_img)
        m = (a > 0).astype(np.uint8)
        lbl, n = ndi.label(m)
        if n <= 1:
            return Image.fromarray((m*255).astype(np.uint8), mode="L")
        sizes = np.bincount(lbl.ravel())
        sizes[0] = 0
        keep = (lbl == sizes.argmax()).astype(np.uint8)
        if keep.sum() < a.size * min_keep:  # 保险：分割失败时退回原mask
            keep = m
        return Image.fromarray((keep*255).astype(np.uint8), mode="L")

    def close_edges(mask, r=2):
        """轻微膨胀+腐蚀（闭运算）平滑边缘"""
        return mask.filter(ImageFilter.MaxFilter(2*r+1)).filter(ImageFilter.MinFilter(2*r+1))

    def crop_to_bbox(img, mask, pad_ratio=0.04):
        """按 mask 外接矩形裁剪并留少量边"""
        bbox = mask.getbbox()
        if not bbox:
            return img
        x0, y0, x1, y1 = bbox
        w, h = img.size
        pad = int(max(w, h) * pad_ratio)
        x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
        x1 = min(w, x1 + pad); y1 = min(h, y1 + pad)
        return img.crop((x0, y0, x1, y1))

    def fit_cell(im):
        """contain 到 cell 尺寸并居中，背景黑"""
        canvas = Image.new("RGBA", (cellW, cellH), (0, 0, 0, 255))
        w, h = im.size
        s = min(cellW / w, cellH / h)
        nw, nh = max(1, int(w*s)), max(1, int(h*s))
        imr = im.resize((nw, nh), Image.LANCZOS)
        x = (cellW - nw) // 2; y = (cellH - nh) // 2
        canvas.alpha_composite(imr, (x, y))
        return canvas

    def _vertical_streak(im_rgba, strength):
        """简易竖向拉丝（上采样再回缩），只对视觉做一点拉丝感"""
        if strength <= 0:
            return im_rgba
        w, h = im_rgba.size
        return im_rgba.resize((w, h + strength), Image.BICUBIC).resize((w, h), Image.LANCZOS)

    def triangle_mask_for_cell(cell_left, cell_top, cell_w, cell_h,
                               canvas_w, canvas_h, apex_x, apex_y, fade_power=1.0,
                               expand_left=0, expand_right=0, top_offset_px=0):
        """
        生成全局三角+渐隐的 mask，并裁到 cell 尺寸。
        底边：以 cell 的"上边"为基准；向内/外扩若干像素；也可整体上移/下移
        """
        # 底边坐标（可扩展和偏移）
        x0 = cell_left - expand_left
        x1 = cell_left + cell_w + expand_right
        y0 = cell_top + top_offset_px

        tri_full = Image.new("L", (canvas_w, canvas_h), 0)
        d = ImageDraw.Draw(tri_full)
        d.polygon([(apex_x, apex_y), (x0, y0), (x1, y0)], fill=255)

        grad = Image.new("L", (canvas_w, canvas_h), 0)
        px = grad.load()
        height = max(1, apex_y - y0)
        for y in range(y0, apex_y + 1):
            t = (y - y0) / height
            val = int((t ** fade_power) * 255)
            for x in range(x0, x1+1):
                px[x, y] = val

        mask_full = ImageChops.multiply(tri_full, grad)
        return mask_full.crop((cell_left, cell_top, cell_left + cell_w, cell_top + cell_h))

    def make_drape_base(upper_cell):
        """'无alpha'的下摆影像（左右通用）"""
        w, h = upper_cell.size
        lower = upper_cell.crop((0, h//2, w, h))
        drape = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        drape.alpha_composite(ImageOps.flip(lower), (0, 0))
        drape = drape.filter(ImageFilter.GaussianBlur(0.8))
        r, g, b, _ = drape.split()
        return Image.merge("RGBA", (r, g, b, Image.new("L", (w, h), 255)))

    def make_center_connector(canvas_size, X3, Y3, X4, Y4, style,
                              apex_x, apex_y,
                              base_expand_ratio, top_offset_ratio,
                              fade_power, streak, blur, intensity, overlap_px,
                              f_drape, b_drape):
        """中央连接层：真正把中缝'填满并上提'"""
        W, H = canvas_size
        cell_w, cell_h = cellW, cellH
        expand = int(cell_w * base_expand_ratio)
        top_y  = Y3 + int(cell_h * top_offset_ratio)

        # 底边左右端点：跨越两格之间的缝，并各自向外"吃"一点，+overlap 避免黑缝
        left_base_x  = X3 + cell_w - expand - overlap_px
        right_base_x = X4 + expand + overlap_px

        tri = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(tri)
        d.polygon([(apex_x, apex_y), (left_base_x, top_y), (right_base_x, top_y)], fill=255)

        grad = Image.new("L", (W, H), 0)
        px = grad.load()
        height = max(1, apex_y - top_y)
        for y in range(top_y, apex_y + 1):
            t = (y - top_y) / height
            val = int((t ** fade_power) * 255)
            for x in range(left_base_x, right_base_x + 1):
                px[x, y] = val
        mask = ImageChops.multiply(tri, grad)

        if style == "silhouette":
            base = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        else:
            from PIL import ImageStat
            def lum(im): return ImageStat.Stat(ImageOps.grayscale(im.convert("RGB"))).mean[0]
            L = int(min(255, ((lum(f_drape)+lum(b_drape))/2) * intensity / 255 * 255))
            base = Image.new("RGBA", (W, H), (L, L, L, 0))

        base.putalpha(mask)
        base = base.filter(ImageFilter.GaussianBlur(blur))
        base = _vertical_streak(base, streak)
        return base

    def to_silhouette(im_rgba, mask):
        """生成纯白衣蒙版"""
        white = Image.new("RGB", im_rgba.size, (255, 255, 255))
        return Image.merge("RGBA", (*white.split(), mask))

    def process_one_side(raw_bytes: bytes, style: str):
        """入：原图；出：单侧 cell 的 RGBA"""
        base = load_and_orient(raw_bytes)
        cut = remove_bg(base)  # 去背景但保留颜色
        alpha = cut.split()[-1]
        alpha_main = largest_component_from_alpha(alpha)
        alpha_clean = close_edges(alpha_main, r=2)

        if style == "silhouette":
            colored = to_silhouette(cut, alpha_clean)  # 白衣蒙版（可选）
        else:
            r, g, b, _ = cut.split()
            colored = Image.merge("RGBA", (r, g, b, alpha_clean))  # 保留颜色与图案

        colored = crop_to_bbox(colored, alpha_clean)
        return fit_cell(colored)

    def build_texture(front_bytes: bytes, back_bytes: bytes, style: str,
                      apex_x_ratio=APEX_X_RATIO_DEFAULT,
                      apex_y_ratio=APEX_Y_RATIO_DEFAULT,
                      center_expand=CENTER_BASE_EXPAND_DEFAULT,
                      center_top_offset=CENTER_TOP_OFFSET_DEFAULT,
                      center_fade=CENTER_FADE_POWER_DEFAULT,
                      center_streak=CENTER_STREAK_DEFAULT,
                      center_blur=CENTER_BLUR_DEFAULT,
                      center_intensity=CENTER_INTENSITY_DEFAULT,
                      overlap_px=OVERLAP_PX_DEFAULT,
                      debug_masks=False) -> bytes:
        f_cell = process_one_side(front_bytes, style)
        b_cell = process_one_side(back_bytes, style)

        # 四格位置
        X1, Y1 = PAD, PAD
        X2, Y2 = PAD*2 + cellW, PAD
        X3, Y3 = PAD, PAD*2 + cellH
        X4, Y4 = PAD*2 + cellW, PAD*2 + cellH

        # 全局 apex（左右与中央"同一个点"）
        apex_x = int(SIZE * float(apex_x_ratio))
        apex_y = int(SIZE * float(apex_y_ratio))

        # 左右下摆影像（无alpha），其透明度完全由"全局三角 mask"控制
        f_drape = make_drape_base(f_cell)
        b_drape = make_drape_base(b_cell)

        # 左右下摆的 mask：底边各自向中缝"吃进" overlap_px，避免裂缝
        f_mask = triangle_mask_for_cell(
            X3, Y3, cellW, cellH, SIZE, SIZE, apex_x, apex_y, FADE_POWER,
            expand_left=0, expand_right=overlap_px, top_offset_px=0
        )
        b_mask = triangle_mask_for_cell(
            X4, Y4, cellW, cellH, SIZE, SIZE, apex_x, apex_y, FADE_POWER,
            expand_left=overlap_px, expand_right=0, top_offset_px=0
        )
        f_drape.putalpha(f_mask)
        b_drape.putalpha(b_mask)

        # 画布
        canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
        canvas.alpha_composite(f_cell, (X1, Y1))
        canvas.alpha_composite(b_cell, (X2, Y2))
        canvas.alpha_composite(f_drape, (X3, Y3))
        canvas.alpha_composite(b_drape, (X4, Y4))

        # 中央连接层（真正"填中缝"的宽三角）
        center = make_center_connector(
            (SIZE, SIZE), X3, Y3, X4, Y4, style,
            apex_x, apex_y,
            base_expand_ratio=center_expand,
            top_offset_ratio=center_top_offset,
            fade_power=center_fade,
            streak=center_streak,
            blur=center_blur,
            intensity=center_intensity,
            overlap_px=overlap_px,
            f_drape=f_drape, b_drape=b_drape
        )
        canvas.alpha_composite(center, (0, 0))

        if debug_masks:
            # 调试：把mask区域微微提亮，便于看"有没有连起来"
            overlay = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 30))
            canvas.alpha_composite(overlay, (0, 0))

        out = canvas.convert("RGB")
        buf = BytesIO(); out.save(buf, format="PNG", optimize=True); buf.seek(0)
        return buf.read()

    # ---- FastAPI ----
    fastapi_app = FastAPI(title="T-shirt Texture API (keep color & logo)")

    @fastapi_app.post("/build-texture")
    async def build_texture_ep(
        front: UploadFile = File(...),
        back: UploadFile = File(...),
        style: str = Query("preserve", enum=["preserve", "silhouette"])
    ):
        try:
            fb = await front.read()
            bb = await back.read()
            if not fb or not bb:
                raise HTTPException(400, "missing files front/back")
            png = build_texture(fb, bb, style)
            return Response(content=png, media_type="image/png",
                            headers={"Content-Disposition": 'inline; filename="texture.png"'})
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"processing_error: {e}")
    
    return fastapi_app
