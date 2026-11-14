"""
基于专利 CN111222503A 与 J-STAGE (JRNAL 2024) 古琴谱论文
生成纯净白底高反差单字切片 (彻底解决模糊与一团黑问题)
"""

from PIL import Image, ImageFilter
import numpy as np
import os
from scipy.ndimage import label

def extract_tight_clean_crop(img, x1, y1, x2, y2, out_path):
    crop = img.crop((x1, y1, x2, y2)).convert('L')
    arr = np.array(crop).astype(np.float32)

    # 1. 局部高斯背景消除 (彻底消除纸张泛黄、反渗透与墨渍)
    bg = np.array(crop.filter(ImageFilter.GaussianBlur(radius=10))).astype(np.float32)
    diff = bg - arr

    # 2. 笔画阈值提取 (差异大于 22 视为墨迹)
    ink_mask = diff > 22

    # 3. 连通域降噪: 滤除纸张微小噪点和背面透字
    labeled, num_features = label(ink_mask)
    if num_features == 0:
        return
    sizes = np.bincount(labeled.ravel())
    # 保留大于 25 像素的真实笔画
    mask_clean = sizes[labeled] > 25

    # 4. 极限紧凑切框 (Tight Bounding Box)
    y_indices, x_indices = np.where(mask_clean)
    if len(y_indices) == 0:
        return
    ymin, ymax = np.min(y_indices), np.max(y_indices)
    xmin, xmax = np.min(x_indices), np.max(x_indices)

    # 上下左右留 3px 纯白边距
    pad = 3
    x_start = max(0, xmin - pad)
    y_start = max(0, ymin - pad)
    x_end = min(crop.width, xmax + pad + 1)
    y_end = min(crop.height, ymax + pad + 1)

    tight_crop = crop.crop((x_start, y_start, x_end, y_end))

    # 5. 归一化为纯白底 (#ffffff) + 浓墨黑 (#111111)
    t_arr = np.array(tight_crop).astype(np.float32)
    t_bg = np.array(tight_crop.filter(ImageFilter.GaussianBlur(radius=8))).astype(np.float32)
    t_diff = t_bg - t_arr

    # 背景绝对纯白 255，深色笔画为 15~25
    val = 255.0 - np.clip((t_diff - 12.0) / 26.0, 0.0, 1.0) * 238.0
    
    out = Image.fromarray(val.astype(np.uint8))
    # 尺寸稍微优化，保持清晰
    out.save(out_path, quality=98)
    print(f"✓ 成功生成纯净单字切片: {out_path} (尺寸: {out.size})")

def main():
    os.makedirs('crops/daoyi', exist_ok=True)
    os.makedirs('crops/chunfeng', exist_ok=True)

    # 1. 处理《捣衣》Line 1 (IMG_0961_line_1.jpg)
    daoyi_line1 = Image.open('slices_daoyi_p6/IMG_0961_line_1.jpg')
    w, h = daoyi_line1.size
    y1 = int(h * 0.56)
    y2 = int(h * 0.98)

    daoyi_crops = {
        'daoyi_m1_1': (648, 745),
        'daoyi_m1_2': (750, 842),
        'daoyi_m1_3': (930, 1026),
        'daoyi_m1_4': (1026, 1128),
        'daoyi_m2_1': (1210, 1320),
        'daoyi_m3_1': (1455, 1555),
        'daoyi_m4_1': (1770, 1885),
        'daoyi_m5_1': (2030, 2130),
        'daoyi_m5_2': (2245, 2365)
    }

    for name, (x1, x2) in daoyi_crops.items():
        out_path = f"crops/daoyi/{name}.png"
        extract_tight_clean_crop(daoyi_line1, x1, y1, x2, y2, out_path)

if __name__ == '__main__':
    main()

