# -*- coding: utf-8 -*-
"""《春风》第 1 页：书页曲面展平 + 全彩去批注 + 2800px SDF 轮廓重建与无损 PNG 编码脚本。

输出目录：program/春风/out_cf_agron_my/
"""
import io, os, json, base64
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import uniform_filter, gaussian_filter, label, distance_transform_edt, maximum_filter

HERE = os.path.dirname(os.path.abspath(__file__))
CF_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "春风"))
OUT_DIR = os.path.join(CF_DIR, "out_cf_agron_my")
PNG_DIR = os.path.join(OUT_DIR, "my_cf_rows")
os.makedirs(PNG_DIR, exist_ok=True)

im = ImageOps.exif_transpose(Image.open(os.path.join(CF_DIR, "IMG_0963.jpeg"))).convert("RGB")
W, H = im.size
arr = np.asarray(im, dtype=np.float32)

x_knots = np.array([0.0, 0.08, 0.20, 0.50, 0.88, 1.00])
y_rows_at_knots = np.array([
    [0.248, 0.243, 0.238, 0.241, 0.245, 0.246], # Row 1
    [0.358, 0.353, 0.348, 0.348, 0.346, 0.345], # Row 2
    [0.478, 0.473, 0.467, 0.462, 0.454, 0.451], # Row 3
    [0.618, 0.612, 0.602, 0.593, 0.577, 0.572], # Row 4
    [0.741, 0.735, 0.725, 0.711, 0.692, 0.686], # Row 5
    [0.869, 0.862, 0.848, 0.828, 0.803, 0.795], # Row 6
])
y_ref = y_rows_at_knots[:, 3]
y_ref_full = np.concatenate([[0.0, 0.14], y_ref, [0.96, 1.0]])
dy_knots = y_rows_at_knots - y_ref[:, None]
dy_full = np.vstack([
    np.zeros((1, len(x_knots))),
    dy_knots[0:1, :] * 0.5,
    dy_knots,
    dy_knots[-1:, :],
    np.zeros((1, len(x_knots))),
])

gx = np.linspace(0, 1, W, dtype=np.float32)
gy = np.linspace(0, 1, H, dtype=np.float32)
dy_at_x = np.zeros((len(y_ref_full), W), dtype=np.float32)
for r_i in range(len(y_ref_full)):
    dy_at_x[r_i] = np.interp(gx, x_knots, dy_full[r_i])
dy_map = np.zeros((H, W), dtype=np.float32)
for x_i in range(W):
    dy_map[:, x_i] = np.interp(gy, y_ref_full, dy_at_x[:, x_i])

y_idx = np.clip((gy[:, None] + dy_map) * H, 0, H - 1)
y0 = np.floor(y_idx).astype(np.int32)
y1 = np.clip(y0 + 1, 0, H - 1)
wy = (y_idx - y0)[..., None]
x_idx = np.arange(W, dtype=np.int32)[None, :]
rect_arr = arr[y0, x_idx] * (1.0 - wy) + arr[y1, x_idx] * wy
rect_im = Image.fromarray(np.clip(rect_arr, 0, 255).astype(np.uint8))

rows_boxes = [
    [0.058, 0.180, 0.865, 0.295], # Row 1
    [0.065, 0.318, 0.865, 0.405], # Row 2
    [0.065, 0.422, 0.865, 0.518], # Row 3
    [0.065, 0.553, 0.885, 0.652], # Row 4
    [0.065, 0.684, 0.900, 0.778], # Row 5
    [0.065, 0.798, 0.925, 0.901], # Row 6
]

erases = [
    # Row 1
    [0.058, 0.180, 0.155, 0.191],
    [0.200, 0.180, 0.312, 0.208],
    [0.495, 0.180, 0.865, 0.218],
    [0.495, 0.218, 0.640, 0.231],
    [0.680, 0.218, 0.865, 0.228],
    [0.141, 0.278, 0.162, 0.295],
    # Row 2
    [0.105, 0.392, 0.150, 0.405],
    [0.238, 0.318, 0.295, 0.335],
    [0.580, 0.318, 0.660, 0.325],
    # Row 4
    [0.065, 0.553, 0.185, 0.575],
    [0.065, 0.575, 0.122, 0.586],
    [0.485, 0.553, 0.580, 0.558],
    [0.588, 0.634, 0.612, 0.650],
    # Row 5
    [0.065, 0.684, 0.096, 0.704],
    [0.128, 0.684, 0.180, 0.691],
    [0.165, 0.684, 0.335, 0.692],
    [0.201, 0.684, 0.335, 0.710],
    [0.110, 0.771, 0.220, 0.785],
    [0.720, 0.768, 0.800, 0.785],
    # Row 6
    [0.065, 0.798, 0.205, 0.818],
    [0.065, 0.818, 0.080, 0.858],
    [0.065, 0.844, 0.118, 0.855],
    [0.315, 0.798, 0.425, 0.825],
    [0.285, 0.848, 0.435, 0.862],
    [0.725, 0.798, 0.805, 0.818],
    [0.735, 0.846, 0.925, 0.856],
    [0.625, 0.840, 0.720, 0.905],
    [0.880, 0.875, 0.925, 0.908],
]

def clean_and_sdf_row(crop_im, er_list, row_idx, out_w=2800):
    a = np.asarray(crop_im, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = (mx - mn) / (mx + 1e-3)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    rg_max = np.maximum(r, g)

    base = rg_max.copy() if row_idx == 4 else lum.copy()
    bg_base = uniform_filter(base, 80)

    is_blue_pen = ((b - r > 15) | (b - g > 12)) & (mn > 35)
    is_orange_pen = (r - g > 18) & (r - b > 22) & (r > 95)
    is_color = is_blue_pen | is_orange_pen | ((sat > 0.20) & (base > 110))

    ch, cw = base.shape
    yg = np.linspace(0, 1, ch)[:, None]
    xg = np.linspace(0, 1, cw)[None, :]
    if row_idx in (1, 2):
        is_color = is_color & (xg > 0.09)
    if row_idx == 6:
        is_color = is_color & ~((xg < 0.07) & (yg > 0.55))

    gray = base.copy()
    gray[is_color] = bg_base[is_color]

    if row_idx == 5:
        arc_mask = (
            ((xg > 0.100) & (xg < 0.132) & (yg >= 0.00) & (yg < 0.085)) |
            ((xg > 0.106) & (xg < 0.160) & (yg > 0.175) & (yg < 0.255)) |
            ((xg > 0.125) & (xg < 0.157) & (yg >= 0.255) & (yg < 0.340)) |
            ((xg > 0.155) & (xg < 0.185) & (yg > 0.90))
        )
        gray[arc_mask] = bg_base[arc_mask]

    if row_idx == 6:
        pencil_c = (xg > 0.042) & (xg < 0.065) & (yg > 0.18) & (yg < 0.52) & (gray > 120)
        gray[pencil_c] = bg_base[pencil_c]

    for rx0, ry0, rx1, ry1 in er_list:
        x0, y0 = max(0, int(rx0 * cw)), max(0, int(ry0 * ch))
        x1, y1 = min(cw, int(rx1 * cw)), min(ch, int(ry1 * ch))
        if x1 > x0 and y1 > y0:
            gray[y0:y1, x0:x1] = bg_base[y0:y1, x0:x1]

    bg2 = uniform_filter(gray, 75)
    norm = np.clip(gray / (bg2 + 1e-3) * 250.0, 0, 255)
    x_w = np.linspace(0, 1, cw, dtype=np.float32)[None, :]
    hi_thr = np.where(x_w < 0.09, 236.0, 226.0)
    lo_thr = np.where(x_w < 0.09, 145.0, 118.0)
    v0 = np.clip((norm - lo_thr) / (hi_thr - lo_thr), 0, 1) * 255.0

    mask1 = v0 < 190.0
    lbl, nfeat = label(mask1)
    if nfeat > 0:
        sz = np.bincount(lbl.ravel())
        v0[(sz[lbl] < 18) & mask1] = 255.0

    v_lap = v0 - 0.5 * (np.roll(v0, 2, axis=0) + np.roll(v0, -2, axis=0))
    h_lap = v0 - 0.5 * (np.roll(v0, 2, axis=1) + np.roll(v0, -2, axis=1))
    g_boost = np.clip(v0 + 1.25 * np.maximum(0, v_lap) + 1.0 * np.maximum(0, h_lap), 0, 255)

    up2 = Image.fromarray(g_boost.astype(np.uint8), 'L').resize((cw * 2, ch * 2), Image.BICUBIC)
    u = np.asarray(up2, dtype=np.float32)
    u_s = gaussian_filter(u, sigma=(1.0, 1.2))
    u_bg = gaussian_filter(u, sigma=(3.5, 3.5))
    u_enh = u_s + 0.85 * (u_s - u_bg)

    ink = u_enh < 115.0
    d_in = distance_transform_edt(ink)
    d_out = distance_transform_edt(~ink)
    sdf = d_out - d_in
    sdf_smooth = gaussian_filter(sdf, sigma=1.35)

    local_thick = maximum_filter(d_in, size=9)
    shift = np.clip((local_thick - 3.2) * 0.22, -0.45, 0.45)
    sdf_adj = sdf_smooth + shift

    v = np.clip((sdf_adj + 0.85) / 1.7, 0.0, 1.0)
    v = v * v * (3.0 - 2.0 * v)
    out_arr = (6.0 + v * (255.0 - 6.0)).astype(np.uint8)
    nh = round(ch * out_w / cw)
    resized = Image.fromarray(out_arr, 'L').resize((out_w, nh), Image.LANCZOS)
    padded = Image.new('L', (out_w, nh + 32), 255)
    padded.paste(resized, (0, 16))
    return padded

if __name__ == "__main__":
    b64_rows = []
    total_kb = 0
    for i, (x0, y0, x1, y1) in enumerate(rows_boxes, 1):
        crop = rect_im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        rel_er = []
        for ex0, ey0, ex1, ey1 in erases:
            if ey1 > y0 and ey0 < y1 and ex1 > x0 and ex0 < x1:
                rel_er.append([
                    (ex0 - x0) / (x1 - x0),
                    (ey0 - y0) / (y1 - y0),
                    (ex1 - x0) / (x1 - x0),
                    (ey1 - y0) / (y1 - y0),
                ])
        im_sdf = clean_and_sdf_row(crop, rel_er, i, out_w=2800)
        out_png = os.path.join(PNG_DIR, f"row_{i}.png")
        im_sdf.save(out_png)

        q = (np.round(np.asarray(im_sdf, dtype=np.float32) / 17.0) * 17.0).astype(np.uint8)
        im_p = Image.fromarray(q, 'L').convert('P', palette=Image.ADAPTIVE, colors=16)
        b = io.BytesIO()
        im_p.save(b, 'PNG', optimize=True)
        raw = b.getvalue()
        total_kb += len(raw) / 1024
        b64_rows.append(base64.b64encode(raw).decode('ascii'))
        print(f"Row {i}: {im_sdf.size}, {len(raw)/1024:.1f} KB")

    print(f"6 rows 2800px lossless PNG total binary size: {total_kb:.1f} KB")
    json.dump(b64_rows, open(os.path.join(OUT_DIR, "my_cf_rows_b64.json"), "w"))
