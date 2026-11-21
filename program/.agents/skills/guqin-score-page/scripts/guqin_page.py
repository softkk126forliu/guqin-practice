#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""古琴「跟谱」页面生成器（Agron 2800px SDF 无损矢量级超清版）：
谱面照片 + spec.json -> 单文件 HTML。

子命令（Pillow + numpy + scipy）：
  rows   spec.json            在展平后的照片上画出每一排的裁切框 -> out/rows_preview.jpg
  clean  spec.json            裁切每一排、去彩笔/荧光笔、2800px SDF 重建 -> out/row_N.png
  ruler  spec.json            在每排画 1% 刻度标尺与 5% 红线 -> out/ruler_rows.jpg（精对位）
  peaks  spec.json [--row N]  列出每排墨迹横向聚类中心(%)，辅助初算 notes[].x
  check  spec.json            把每个音的格子画在行图上 -> out/check_N.jpg & out/check_all.jpg
  build  spec.json            生成最终单文件 HTML（内嵌 16 阶无损 PNG）
"""
import argparse, base64, io, json, os, re, sys
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

try:
    from scipy.ndimage import (
        uniform_filter,
        gaussian_filter,
        label,
        binary_opening,
        distance_transform_edt,
        maximum_filter,
    )
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "page.template.html")
ROW_W = 2800            # 输出行图宽度（2800px 超清）
CELL_W = 3.20           # 默认单音格子宽度(行宽 %)
MAJOR = [0, 2, 4, 5, 7, 9, 11]
ACC = {"#": 1, "♯": 1, "b": -1, "♭": -1}
TONIC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NM_SHARP = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]
NM_FLAT = ["C", "D♭", "D", "E♭", "E", "F", "G♭", "G", "A♭", "A", "B♭", "B"]


def tonic_pc(s):
    """'bB' / '♭B' / 'F#' / 'C' -> 0..11"""
    s = s.strip()
    acc = 0
    while s and s[0] in ACC:
        acc += ACC[s[0]]
        s = s[1:]
    base = TONIC[s[0].upper()]
    for ch in s[1:]:
        acc += ACC.get(ch, 0)
    return (base + acc) % 12


def note_names_for_tonic(s):
    return NM_FLAT if ("b" in s or "♭" in s or s.strip().upper() == "F") else NM_SHARP


def digit_pc(tok, tonic):
    """简谱音符 '6' '#4' 'b7' '7#' -> 音级(0..11)。"""
    tok = str(tok).strip()
    acc = 0
    for ch in tok:
        acc += ACC.get(ch, 0)
    d = int(re.sub(r"[^1-7]", "", tok))
    return (tonic + MAJOR[d - 1] + acc) % 12


def load_spec(path):
    spec = json.load(open(path, encoding="utf-8"))
    spec["_dir"] = os.path.dirname(os.path.abspath(path))
    spec.setdefault("out", "out")
    return spec


def P(spec, rel):
    return rel if os.path.isabs(rel) else os.path.join(spec["_dir"], rel)


def rectify_curved_page(im, x_knots, y_rows_at_knots):
    """按给定的行中心控制点 (x_knots, y_rows_at_knots) 将书页弯曲与倾斜展平。"""
    W, H = im.size
    arr = np.asarray(im, dtype=np.float32)
    xk = np.asarray(x_knots, dtype=np.float32)
    yk = np.asarray(y_rows_at_knots, dtype=np.float32)
    ref_idx = len(xk) // 2
    y_ref = yk[:, ref_idx]
    y_ref_full = np.concatenate([[0.0, max(0.05, float(y_ref[0]) - 0.10)], y_ref, [min(0.98, float(y_ref[-1]) + 0.12), 1.0]])
    dy_knots = yk - y_ref[:, None]
    dy_full = np.vstack([
        np.zeros((1, len(xk))),
        dy_knots[0:1, :] * 0.5,
        dy_knots,
        dy_knots[-1:, :],
        np.zeros((1, len(xk))),
    ])
    gx = np.linspace(0, 1, W, dtype=np.float32)
    gy = np.linspace(0, 1, H, dtype=np.float32)
    dy_at_x = np.zeros((len(y_ref_full), W), dtype=np.float32)
    for r_i in range(len(y_ref_full)):
        dy_at_x[r_i] = np.interp(gx, xk, dy_full[r_i])
    dy_map = np.zeros((H, W), dtype=np.float32)
    for x_i in range(W):
        dy_map[:, x_i] = np.interp(gy, y_ref_full, dy_at_x[:, x_i])
    y_idx = np.clip((gy[:, None] + dy_map) * H, 0, H - 1)
    y0 = np.floor(y_idx).astype(np.int32)
    y1 = np.clip(y0 + 1, 0, H - 1)
    wy = (y_idx - y0)[..., None]
    x_idx = np.arange(W, dtype=np.int32)[None, :]
    rect_arr = arr[y0, x_idx] * (1.0 - wy) + arr[y1, x_idx] * wy
    return Image.fromarray(np.clip(rect_arr, 0, 255).astype(np.uint8))


def open_photo(spec):
    im = ImageOps.exif_transpose(Image.open(P(spec, spec["photo"])))
    rot = spec.get("rotate", 0)
    if rot:
        im = im.rotate(rot, expand=True, fillcolor=(255, 255, 255))
    im = im.convert("RGB")
    if spec.get("x_knots") and spec.get("y_rows_at_knots"):
        im = rectify_curved_page(im, spec["x_knots"], spec["y_rows_at_knots"])
    return im


def crop_box(im, box):
    w, h = im.size
    return im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))


def clean_double_beams(g):
    """修复扫描谱中双减时线 '=' 粘连成黑块的问题。"""
    dark = g < 160
    horiz = binary_opening(dark, structure=np.ones((1, 16)))
    H, W = g.shape
    out = g.copy()
    for y in range(2, H - 2):
        gap = (horiz[y - 2] & horiz[y + 2]) | (horiz[y - 2] & horiz[y + 1]) | (horiz[y - 1] & horiz[y + 2])
        lbl, n = label(gap)
        for k in range(1, n + 1):
            xs = np.where(lbl == k)[0]
            if len(xs) >= 10:
                band = g[y - 1 : y + 2, xs]
                best_dy = np.argmax(band.mean(axis=1)) - 1
                ry = y + best_dy
                if g[ry, xs].max() > 140:
                    out[ry, xs] = np.maximum(out[ry, xs], 250.0)
    return out


def clean_row_sdf(img, row, out_w=ROW_W):
    """Agron 超清管线：自动适配扫描黑白谱(4x SDF)与实拍彩笔批注书页(去彩笔/荧光笔 + 2x SDF)，输出 2800px 超清行图。"""
    if row.get("rotate"):
        img = img.rotate(row["rotate"], expand=True, fillcolor=(255, 255, 255))
    if not HAS_SCIPY:
        a = np.asarray(img).astype(np.int16)
        sat = a.max(axis=2) - a.min(axis=2)
        thr = row.get("color_thr", 38)
        colored = Image.fromarray(((sat > thr) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
        cm = np.asarray(colored) > 0
        gray = np.asarray(img.convert("L")).astype(np.float32)
        fill = np.median(gray[~cm]) if (~cm).any() else 235
        g2 = np.where(cm, fill, gray)
        bg = np.asarray(Image.fromarray(g2.astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(12, img.width // 60)))).astype(np.float32)
        flat = np.clip(g2 / np.maximum(bg, 1) * 255, 0, 255)
        lo, hi = row.get("black", 120), row.get("white", 225)
        v = np.clip((flat - lo) / (hi - lo), 0, 1)
        v = v * v * (3 - 2 * v) * 255
        v[cm] = 255
        h, w = v.shape
        for e in row.get("erase", []):
            v[int(e[1] * h):int(e[3] * h), int(e[0] * w):int(e[2] * w)] = 255
        out = Image.fromarray(v.astype(np.uint8), "L")
        nh = round(out.height * out_w / out.width)
        return out.resize((out_w, nh), Image.LANCZOS)

    a = np.asarray(img, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = (mx - mn) / (mx + 1e-3)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    ch, cw = lum.shape

    # 判断是否为低分辨率黑白扫描谱（无彩笔且原图宽 < 1500）
    is_clean_scan = row.get("scan_mode", (cw < 1500 and float((mx - mn).max()) < 30.0))

    if is_clean_scan:
        v0 = lum.copy()
        for rx0, ry0, rx1, ry1 in row.get("erase", []):
            x0, y0 = max(0, int(rx0 * cw)), max(0, int(ry0 * ch))
            x1, y1 = min(cw, int(rx1 * cw)), min(ch, int(ry1 * ch))
            if x1 > x0 and y1 > y0:
                v0[y0:y1, x0:x1] = 255.0
        v0 = clean_double_beams(v0)
        mask1 = v0 < 190.0
        lbl, nfeat = label(mask1)
        if nfeat > 0:
            sz = np.bincount(lbl.ravel())
            v0[(sz[lbl] < 5) & mask1] = 255.0
            for k in range(1, nfeat + 1):
                ys, xs = np.where(lbl == k)
                ymin, ymax, xmin, xmax = ys.min(), ys.max(), xs.min(), xs.max()
                bw, bh = xmax - xmin + 1, ymax - ymin + 1
                if ymax < ch * 0.30 and 6 <= bw <= 9 and 6 <= bh <= 9:
                    cy, cx = (ymin + ymax) // 2, (xmin + xmax) // 2
                    if v0[cy - 1 : cy + 2, cx - 1 : cx + 2].max() > 150:
                        v0[cy - 1 : cy + 2, cx - 1 : cx + 2] = np.maximum(v0[cy - 1 : cy + 2, cx - 1 : cx + 2], 250.0)
        v_lap = v0 - 0.5 * (np.roll(v0, 1, axis=0) + np.roll(v0, -1, axis=0))
        h_lap = v0 - 0.5 * (np.roll(v0, 1, axis=1) + np.roll(v0, -1, axis=1))
        g_boost = np.clip(v0 + 1.4 * np.maximum(0, v_lap) + 1.1 * np.maximum(0, h_lap), 0, 255)
        up = Image.fromarray(g_boost.astype(np.uint8), "L").resize((cw * 4, ch * 4), Image.BICUBIC)
        u = np.asarray(up, dtype=np.float32)
        u_s = gaussian_filter(u, sigma=(0.9, 1.15))
        u_bg = gaussian_filter(u, sigma=(3.0, 3.0))
        u_enh = u_s + 0.92 * (u_s - u_bg)
        ink = u_enh < 64.0
        d_in = distance_transform_edt(ink)
        d_out = distance_transform_edt(~ink)
        sdf = d_out - d_in
        sdf_smooth = gaussian_filter(sdf, sigma=1.35)
        local_thick = maximum_filter(d_in, size=9)
        shift = np.clip((local_thick - 3.0) * 0.26, -0.48, 0.48)
        sdf_adj = sdf_smooth + shift
        v = np.clip((sdf_adj + 0.80) / 1.6, 0.0, 1.0)
        v = v * v * (3.0 - 2.0 * v)
        out_arr = (6.0 + v * (255.0 - 6.0)).astype(np.uint8)
        nh = round(ch * out_w / cw)
        resized = Image.fromarray(out_arr, "L").resize((out_w, nh), Image.LANCZOS)
        pad = int(row.get("pad_y", 0))
    else:
        rg_max = np.maximum(r, g)
        base = rg_max.copy() if row.get("highlighter") else lum.copy()
        bg_base = uniform_filter(base, 80)

        is_blue_pen = ((b - r > 15) | (b - g > 12)) & (mn > 35)
        is_orange_pen = (r - g > 18) & (r - b > 22) & (r > 95)
        sat_thr = row.get("sat_thr", 0.20)
        is_color = is_blue_pen | is_orange_pen | ((sat > sat_thr) & (base > 110))

        yg = np.linspace(0, 1, ch)[:, None]
        xg = np.linspace(0, 1, cw)[None, :]
        protect_left = row.get("protect_left", 0.0)
        if protect_left > 0:
            is_color = is_color & (xg > protect_left)
        for px0, py0, px1, py1 in row.get("protect_boxes", []):
            is_color = is_color & ~((xg >= px0) & (xg <= px1) & (yg >= py0) & (yg <= py1))

        gray = base.copy()
        gray[is_color] = bg_base[is_color]

        for rx0, ry0, rx1, ry1 in row.get("erase", []):
            x0, y0 = max(0, int(rx0 * cw)), max(0, int(ry0 * ch))
            x1, y1 = min(cw, int(rx1 * cw)), min(ch, int(ry1 * ch))
            if x1 > x0 and y1 > y0:
                gray[y0:y1, x0:x1] = bg_base[y0:y1, x0:x1]

        bg2 = uniform_filter(gray, 75)
        norm = np.clip(gray / (bg2 + 1e-3) * 250.0, 0, 255)
        lo_default = float(row.get("black", 118.0))
        hi_default = float(row.get("white", 226.0))
        if protect_left > 0:
            x_w = np.linspace(0, 1, cw, dtype=np.float32)[None, :]
            hi_thr = np.where(x_w < protect_left, max(hi_default, 236.0), hi_default)
            lo_thr = np.where(x_w < protect_left, max(lo_default, 145.0), lo_default)
        else:
            hi_thr = hi_default
            lo_thr = lo_default

        v0 = np.clip((norm - lo_thr) / (hi_thr - lo_thr), 0, 1) * 255.0

        mask1 = v0 < 190.0
        lbl, nfeat = label(mask1)
        if nfeat > 0:
            sz = np.bincount(lbl.ravel())
            v0[(sz[lbl] < 16) & mask1] = 255.0

        v_lap = v0 - 0.5 * (np.roll(v0, 2, axis=0) + np.roll(v0, -2, axis=0))
        h_lap = v0 - 0.5 * (np.roll(v0, 2, axis=1) + np.roll(v0, -2, axis=1))
        g_boost = np.clip(v0 + 1.25 * np.maximum(0, v_lap) + 1.0 * np.maximum(0, h_lap), 0, 255)

        up2 = Image.fromarray(g_boost.astype(np.uint8), "L").resize((cw * 2, ch * 2), Image.BICUBIC)
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
        resized = Image.fromarray(out_arr, "L").resize((out_w, nh), Image.LANCZOS)
        pad = int(row.get("pad_y", 16))

    if pad > 0:
        padded = Image.new("L", (out_w, nh + pad * 2), 255)
        padded.paste(resized, (0, pad))
        return padded
    return resized


def row_images(spec):
    """返回每排的 L 模式行图。row.image 已有干净图时直接用，否则从照片裁切+SDF超清清洗。"""
    ims = []
    photos = {}
    out_w = int(spec.get("row_w", ROW_W))
    for r in spec["rows"]:
        if r.get("image"):
            im = Image.open(P(spec, r["image"])).convert("L")
            if im.width != out_w:
                im = im.resize((out_w, round(im.height * out_w / im.width)), Image.LANCZOS)
            ims.append(im)
        else:
            name = r.get("photo") or spec["photo"]
            if name not in photos:
                s = dict(spec)
                s["photo"] = name
                photos[name] = open_photo(s)
            crop = crop_box(photos[name], r["box"])
            # Merge global spec["erases"] overlapping with r["box"] into row-relative erase boxes
            r_copy = dict(r)
            rel_er = list(r.get("erase", []))
            x0, y0, x1, y1 = r["box"]
            for ex0, ey0, ex1, ey1 in spec.get("erases", []):
                if ey1 > y0 and ey0 < y1 and ex1 > x0 and ex0 < x1:
                    rel_er.append([
                        (ex0 - x0) / (x1 - x0),
                        (ey0 - y0) / (y1 - y0),
                        (ex1 - x0) / (x1 - x0),
                        (ey1 - y0) / (y1 - y0),
                    ])
            r_copy["erase"] = rel_er
            ims.append(clean_row_sdf(crop, r_copy, out_w=out_w))
    return ims


def outdir(spec):
    d = P(spec, spec["out"])
    os.makedirs(d, exist_ok=True)
    return d


def cmd_rows(spec):
    """在原图上画出每一排的裁切框 -> out/rows_preview.jpg。
    spec 支持逐排指定 photo（跨多张书页照片时），此时按原图分组分别生成预览。"""
    groups = {}
    for i, r in enumerate(spec["rows"]):
        if "box" not in r:
            continue
        name = r.get("photo") or spec.get("photo")
        if not name:
            continue
        groups.setdefault(name, []).append((i, r))

    outs = []
    for name, items in groups.items():
        s = dict(spec)
        s["photo"] = name
        im = open_photo(s)
        d = ImageDraw.Draw(im)
        w, h = im.size
        for i, r in items:
            b = r["box"]
            xy = [b[0] * w, b[1] * h, b[2] * w, b[3] * h]
            d.rectangle(xy, outline=(255, 0, 0), width=max(3, w // 400))
            d.text((xy[0] + 6, xy[1] + 4), f"row {i+1}", fill=(255, 0, 0))
        im.thumbnail((1800, 1800))
        stem = os.path.splitext(os.path.basename(name))[0]
        p = os.path.join(outdir(spec), f"rows_preview_{stem}.jpg" if len(groups) > 1 else "rows_preview.jpg")
        im.save(p, quality=88)
        print(p)
        outs.append(p)
    if not outs:
        print("没有可预览的排（spec 需提供 box 与 photo）")


def cmd_clean(spec):
    od = outdir(spec)
    for i, im in enumerate(row_images(spec)):
        p = os.path.join(od, f"row_{i+1}.png")
        im.save(p)
        print(p, im.size)


def cmd_ruler(spec):
    """在每排超清行图上绘制 1% 刻度与 5% 红线，方便精准测量每个音符(含倚音+减字谱)的 x 和 w。"""
    ims = [im.convert("RGB") for im in row_images(spec)]
    for ri, im in enumerate(ims):
        dr = ImageDraw.Draw(im)
        W, H = im.size
        for pct in range(0, 100):
            x = int(pct / 100.0 * W)
            if pct % 5 == 0:
                dr.line([(x, 0), (x, H)], fill=(220, 60, 60), width=2)
                dr.text((x + 3, 2), f"{pct}", fill=(200, 0, 0))
            else:
                dr.line([(x, 0), (x, 22)], fill=(120, 160, 220), width=1)
                dr.line([(x, H - 22), (x, H)], fill=(120, 160, 220), width=1)
        dr.text((10, H // 2 - 10), f"R{ri+1}", fill=(0, 120, 0))
    out_im = Image.new("RGB", (ims[0].width, sum(x.height for x in ims)), (255, 255, 255))
    y_acc = 0
    for im in ims:
        out_im.paste(im, (0, y_acc))
        y_acc += im.height
    p = os.path.join(outdir(spec), "ruler_rows.jpg")
    out_im.resize((1800, int(out_im.height * 1800 / out_im.width))).save(p, quality=92)
    print(p)


def cmd_peaks(spec, only=None):
    for i, im in enumerate(row_images(spec)):
        if only and i + 1 != only:
            continue
        r = spec["rows"][i]
        y0, y1 = r.get("band", [0, 1])
        a = np.asarray(im).astype(np.float32)
        H, W = a.shape
        ink = (255 - a[int(y0 * H):int(y1 * H)]).sum(axis=0)
        on = ink > ink.max() * 0.04
        res, s = [], None
        for x in range(W + 1):
            f = on[x] if x < W else False
            if f and s is None:
                s = x
            if not f and s is not None:
                if x - s > 3:
                    res.append(((s + x) / 2 / W * 100, (x - s) / W * 100))
                s = None
        m = []
        for c, wd in res:
            if m and c - m[-1][0] < 1.2:
                m[-1] = ((m[-1][0] + c) / 2, max(m[-1][1], wd))
            else:
                m.append((c, wd))
        print(f"row {i+1} 有 {len(m)} 个墨迹块；中心(%)=", [round(c, 1) for c, _ in m])
        print(f"   对应 notes[].x ≈ 中心 - {CELL_W/2:.2f}")


def parse_note_p(n):
    """兼容 p: ['6','3'] 或 p: '6/3' 或 rest: true / p: '0'。
    有显式 pc（音高）但没有 p（简谱数字）的音符仍算可弹奏音，不是休止符；
    但 p 显式写成 '0' / '-' 表示简谱休止，仍按休止符处理。"""
    if n.get("rest"):
        return [], True
    raw = n.get("p", [])
    if isinstance(raw, str):
        raw = raw.strip()
        if raw in ("0", "-"):
            return [], True          # 简谱明确写 0/- 表示休止
        if raw == "":
            # p 为空但给了 pc：音高明确，视为可弹奏音
            return [], False
        return [x.strip() for x in raw.split("/") if x.strip()], False
    p_list = [str(x).strip() for x in raw if str(x).strip()]
    if p_list == ["0"]:
        return [], True              # 简谱明确写 0 表示休止
    if not p_list:
        # p 缺省：pc 存在则视为可弹奏音
        return [], False
    return p_list, False


def build_cells_and_rows(spec, ims):
    tonic = tonic_pc(spec.get("tonic", "C"))
    rows_meta = []
    cells = []
    for ri, r in enumerate(spec["rows"]):
        im = ims[ri]
        r_notes = r.get("notes", [])
        rows_meta.append({
            "w": im.width,
            "h": im.height,
            "bpm": r.get("bpm", 60),
            "count": len(r_notes),
        })
        row_harm = r.get("harm", False)
        for ni, n in enumerate(r_notes):
            p_strs, is_rest = parse_note_p(n)
            rest = 1 if is_rest else 0
            if rest:
                pcs = []
            elif "pc" in n:
                pcs = n["pc"]
            else:
                pcs = [digit_pc(t, tonic) for t in p_strs]
            # 有 pc 无 p 的音也算双音结构宽度的一半；没有音高信息时退回单音宽度
            default_w = 3.80 if (len(p_strs) >= 2 or len(pcs) >= 2) else CELL_W
            w = round(float(n.get("w", default_w)), 2)
            x = round(float(n["x"]), 2)
            harm = 1 if (not rest and n.get("harm", row_harm)) else 0
            cells.append({
                "r": ri,
                "ni": ni,
                "p": p_strs,
                "pcs": pcs,
                "x": x,
                "w": w,
                "d": n["d"],
                "rest": rest,
                "harm": harm,
                # 谱面八度点标记：u1=上方1个实心点 u2=上方2个 d1=下方1个
                "dot": ("" if rest else str(n.get("dot", "") or "")),
            })
    return rows_meta, cells


def cmd_check(spec):
    ims = row_images(spec)
    _, cells = build_cells_and_rows(spec, ims)
    NM = note_names_for_tonic(spec.get("tonic", "C"))
    od = outdir(spec)
    rgb_rows = []
    for i, im in enumerate(ims):
        rgb = im.convert("RGB")
        d = ImageDraw.Draw(rgb, "RGBA")
        W, H = rgb.size
        k = 0
        for c in cells:
            if c["r"] != i:
                continue
            k += 1
            x0 = c["x"] / 100.0 * W
            x1 = (c["x"] + c["w"]) / 100.0 * W
            y0, y1 = H * 0.015, H * 0.985
            d.rectangle([x0, y0, x1, y1], outline=(184, 55, 40, 220), fill=(184, 55, 40, 35), width=3)
            d.text((x0 + 3, 2), str(k), fill=(200, 0, 0))
            lbl = "休" if c["rest"] else "/".join(NM[p] for p in c["pcs"][:2])
            d.text((x0 + 3, H - 16), lbl, fill=(0, 120, 0))
        p = os.path.join(od, f"check_{i+1}.jpg")
        rgb.save(p, quality=90)
        rgb_rows.append(rgb)
        print(p, f"{k} 个音")
    if rgb_rows:
        all_im = Image.new("RGB", (rgb_rows[0].width, sum(r.height for r in rgb_rows)), (252, 249, 240))
        y_acc = 0
        for r_im in rgb_rows:
            all_im.paste(r_im, (0, y_acc))
            y_acc += r_im.height
        all_p = os.path.join(od, "check_all.jpg")
        all_im.resize((1600, int(all_im.height * 1600 / all_im.width))).save(all_p, quality=90)
        print(all_p)


def b64_lossless_png(im):
    """16 阶灰度自适应调色板无损 PNG 编码（彻底消除 JPEG 蚊子噪点且体积小巧）。"""
    q = (np.round(np.asarray(im, dtype=np.float32) / 17.0) * 17.0).astype(np.uint8)
    im_p = Image.fromarray(q, "L").convert("P", palette=Image.ADAPTIVE, colors=16)
    b = io.BytesIO()
    im_p.save(b, "PNG", optimize=True)
    return base64.b64encode(b.getvalue()).decode("ascii")


def cmd_build(spec):
    ims = row_images(spec)
    rows_meta, cells = build_cells_and_rows(spec, ims)
    for i, r in enumerate(rows_meta):
        if r["count"] == 0:
            sys.exit(f"第{i+1}排没有音符")
    t = open(TEMPLATE, encoding="utf-8").read()
    nm = note_names_for_tonic(spec.get("tonic", "C"))
    rep = {
        "@@TITLE@@": spec["title"],
        "@@SUBTITLE@@": spec.get("subtitle", ""),
        "@@IMGS@@": json.dumps([b64_lossless_png(i) for i in ims]),
        "@@ROWS@@": json.dumps(rows_meta),
        "@@CELLS@@": json.dumps(cells, ensure_ascii=False),
        "@@NM@@": json.dumps(nm, ensure_ascii=False),
    }
    for k, v in rep.items():
        t = t.replace(k, v)
    out = P(spec, spec.get("html", f"古琴跟谱 · {spec['title']}.html"))
    open(out, "w", encoding="utf-8").write(t)
    print(out, f"{os.path.getsize(out)//1024} KB, {len(cells)} 个音, {len(ims)} 排")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["rows", "clean", "ruler", "peaks", "check", "build"])
    ap.add_argument("spec")
    ap.add_argument("--row", type=int)
    a = ap.parse_args()
    s = load_spec(a.spec)
    {
        "rows": cmd_rows,
        "clean": cmd_clean,
        "ruler": cmd_ruler,
        "check": cmd_check,
        "build": cmd_build,
    }.get(a.cmd, lambda s: cmd_peaks(s, a.row))(s)
