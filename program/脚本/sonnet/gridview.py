# -*- coding: utf-8 -*-
"""按排输出带网格标尺的谱面分段图，供目视校准音符位置。

用法: py -3.12 gridview.py <row> [spec路径]

spec 默认取 模板/baisuzhen-spec.json（相对本脚本上两级目录）。
行图由 scripts/guqin_page.py 的 row_images 逻辑重建（与最终页面完全一致），
因此本脚本与新版 2800px SDF 流程保持一致，无需再维护写死的像素区间。
"""
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.dirname(os.path.dirname(HERE))
SKILL_SCRIPTS = os.path.join(PROGRAM, '.agents', 'skills', 'guqin-score-page', 'scripts')

if SKILL_SCRIPTS not in sys.path:
    sys.path.append(SKILL_SCRIPTS)
import guqin_page as gp

ROW = int(sys.argv[1])
spec_path = sys.argv[2] if len(sys.argv) >= 3 else os.path.join(PROGRAM, '模板', 'baisuzhen-spec.json')
if not os.path.isabs(spec_path):
    spec_path = os.path.abspath(spec_path)

spec = gp.load_spec(spec_path)
ims = gp.row_images(spec)
if ROW < 1 or ROW > len(ims):
    sys.exit(f'排号超出范围: 1-{len(ims)}')

im = ims[ROW - 1].convert('RGB')
W, H = im.size
from PIL import Image, ImageDraw
d = ImageDraw.Draw(im)
# 1% 蓝刻度 + 5% 红线，与 guqin_page.py ruler 命令一致
for pct in range(0, 100):
    x = int(pct / 100.0 * W)
    if pct % 5 == 0:
        d.line([(x, 0), (x, H)], fill=(220, 60, 60), width=2)
        d.text((x + 3, 2), str(pct), fill=(200, 0, 0))
    else:
        d.line([(x, 0), (x, 22)], fill=(120, 160, 220), width=1)
        d.line([(x, H - 22), (x, H)], fill=(120, 160, 220), width=1)
d.text((10, H // 2 - 10), f'R{ROW}', fill=(0, 120, 0))

half = W // 2
for k, (a, b) in enumerate([(0, half + 30), (half - 30, W)]):
    c = im.crop((a, 0, b, H))
    c = c.resize((int(c.width * 0.75), int(c.height * 0.75)), Image.LANCZOS)
    out = f'D:/tmp/gv_r{ROW}_{k}.jpg'
    c.save(out, quality=95)
    print(f'{out}  {c.size}  覆盖 {a / W * 100:.0f}%-{b / W * 100:.0f}%')
