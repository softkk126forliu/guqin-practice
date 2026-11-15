# -*- coding: utf-8 -*-
"""按行输出简谱带网格分段图，供目视重读。

用法: py -3.12 gridview.py <row> [y0 y1] [spec路径]

spec 默认为当前目录的 baisuzhen-spec.json；行图路径按 spec 所在目录解析。
BANDS 为青城山下白素贞各行的像素区间，其他曲子请自行标定或直接传入 y0 y1。
"""
import sys, json, os
from PIL import Image, ImageDraw

ROW = int(sys.argv[1])
BANDS = {1:(13,84),2:(4,90),3:(7,63),4:(3,70),5:(12,68),6:(5,77),7:(10,69),8:(10,64),
         9:(50,115),10:(0,101),11:(17,78),12:(16,85),13:(38,111),14:(70,155),15:(25,103)}
y0, y1 = BANDS[ROW]
if len(sys.argv) >= 4:
    y0, y1 = int(sys.argv[2]), int(sys.argv[3])

spec_path = sys.argv[4] if len(sys.argv) >= 5 else 'baisuzhen-spec.json'
spec_dir = os.path.dirname(os.path.abspath(spec_path))
spec = json.load(open(spec_path, encoding='utf-8'))
r = spec['rows'][ROW-1]
img_path = r['image']
if not os.path.isabs(img_path):
    img_path = os.path.join(spec_dir, img_path)
im = Image.open(img_path).convert('RGB')
W, H = im.size
d = ImageDraw.Draw(im)
for p in range(0, 101, 5):
    x = int(W*p/100)
    d.line([(x, y0), (x, y1)], fill=(255,0,0), width=1)
    d.text((x+2, y1-16), str(p), fill=(255,0,0))
# 行号
d.text((4, y0+2), f'row{ROW} y{y0}-{y1}', fill=(0,0,255))

half = W//2
for k, (a, b) in enumerate([(0, half+30), (half-30, W)]):
    c = im.crop((a, max(0,y0-6), b, min(H,y1+6)))
    c = c.resize((c.width*3, c.height*3), Image.LANCZOS)
    c.save(f'D:/tmp/gv_r{ROW}_{k}.jpg', quality=95)
    print(f'D:/tmp/gv_r{ROW}_{k}.jpg  {c.size}  覆盖 {a/W*100:.0f}%-{b/W*100:.0f}%')
