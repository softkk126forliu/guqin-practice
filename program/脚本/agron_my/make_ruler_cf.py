# -*- coding: utf-8 -*-
"""在 2800px 单行切图上绘制 1% 标尺网格，用于精确读取每个音（简谱+减字谱）的左边界 x 与宽度 w。"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "春风", "out_cf_agron_my"))
PNG_DIR = os.path.join(OUT_DIR, "my_cf_rows")

ims = []
for r in range(1, 7):
    im = Image.open(os.path.join(PNG_DIR, f"row_{r}.png")).convert("RGB")
    W, H = im.size
    dr = ImageDraw.Draw(im, "RGBA")
    for pct in range(0, 101):
        x = int(pct / 100.0 * W)
        if pct % 5 == 0:
            dr.line([(x, 0), (x, H)], fill=(0, 120, 255, 110), width=2)
            dr.text((x + 3, 2), str(pct), fill=(0, 80, 200, 255))
            dr.text((x + 3, H - 18), str(pct), fill=(0, 80, 200, 255))
        else:
            dr.line([(x, 0), (x, H)], fill=(0, 120, 255, 45), width=1)
    ims.append(im)

out1 = Image.new("RGB", (2800, sum(im.height for im in ims[:3])), (255, 255, 255))
y = 0
for im in ims[:3]:
    out1.paste(im, (0, y))
    y += im.height
out1.resize((2000, int(out1.height * 2000 / 2800))).save(os.path.join(OUT_DIR, "ruler_rows_1_2_3.jpg"), quality=90)

out2 = Image.new("RGB", (2800, sum(im.height for im in ims[3:])), (255, 255, 255))
y = 0
for im in ims[3:]:
    out2.paste(im, (0, y))
    y += im.height
out2.resize((2000, int(out2.height * 2000 / 2800))).save(os.path.join(OUT_DIR, "ruler_rows_4_5_6.jpg"), quality=90)
print("Saved ruler_rows_1_2_3.jpg and ruler_rows_4_5_6.jpg in", OUT_DIR)
