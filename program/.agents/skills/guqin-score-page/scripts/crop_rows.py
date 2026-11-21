# -*- coding: utf-8 -*-
"""按 spec 的 box 裁出每排行图，并给每个音标注序号 —— 人工/AI 标注用。

用法：
    python crop_rows.py --spec 模板/baisuzhen-spec.json --out D:/tmp/gq_rows
    python crop_rows.py --spec 春风/chunfeng-p1-spec.json --out D:/tmp/gq_rows_cf

产物（每排两个）：
    row_N.png        整排（简谱行 + 减字谱行），2800px 宽
    row_N_marks.png  简谱区放大 + 每个音上方标出序号（对应 spec 的 notes 顺序）

为什么要有 marks 图：
  简谱数字旁的「下加横线」条数表示减八度（一条 = 低八度），
  是客观可数的判读依据。marks 图把序号标在数字正上方，
  标记者只需按序号逐个报「几条线」。
"""
import argparse
import json
import os

from PIL import Image, ImageDraw

ROW_W = 2800


def load_spec(path):
    spec = json.load(open(path, encoding="utf-8"))
    spec["_dir"] = os.path.dirname(os.path.abspath(path))
    return spec


def P(spec, rel):
    return rel if os.path.isabs(rel) else os.path.join(spec["_dir"], rel)


def split_row(crop, spec_row):
    """把整排切成「简谱区」与「减字谱区」。

    简谱区 = 该排 notes 的 y 区间（box 内）；减字谱区 = box 内其余墨迹。
    这里用简单启发：box 内下半部分若有连续墨迹即为减字谱。
    实际使用中 marks 图只需覆盖简谱数字与其上下记号，所以取 box 的上 2/3。
    """
    h = crop.size[1]
    return crop.crop((0, 0, crop.width, int(h * 0.62)))


def build(spec, out_dir, row_w=ROW_W, marked=True):
    os.makedirs(out_dir, exist_ok=True)
    photos = {}
    made = []

    for ri, r in enumerate(spec["rows"], 1):
        if "box" not in r:
            continue
        name = r.get("photo") or spec.get("photo")
        if not name:
            continue
        if name not in photos:
            photos[name] = Image.open(P(spec, name)).convert("L")
        im = photos[name]
        W, H = im.size
        x0, y0, x1, y1 = r["box"]
        crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        # 缩放到 row_w（保持比例）
        nh = max(1, round(crop.height * row_w / crop.width))
        full = crop.resize((row_w, nh), Image.LANCZOS)
        full.save(os.path.join(out_dir, "row_%d.png" % ri))

        if marked:
            notes = r.get("notes", [])
            simp = split_row(full, r).convert("RGB")
            d = ImageDraw.Draw(simp)
            # 音在行内的水平位置：note.x 是行内百分比（0-100）
            for ni, n in enumerate(notes, 1):
                nx = n.get("x")
                if nx is None:
                    continue
                px = nx / 100.0 * simp.width
                # 序号旁同时标出 spec 的音级 —— note.x 与实际数字位置可能有偏差
                # （撮/叠写处尤甚），标出音级可让标注者当场交叉验证，
                # 避免张冠李戴（实测排3 曾把「3/4」读成「4/5」）。
                p = n.get("p")
                if isinstance(p, list):
                    lbl = "/".join(str(x).strip() for x in p if x is not None and str(x).strip())
                else:
                    lbl = "" if p is None else str(p).strip()
                d.text((px - 6, 2), str(ni), fill=(180, 40, 40))
                d.text((px + 12, 2), lbl, fill=(20, 90, 160))
            simp.save(os.path.join(out_dir, "row_%d_marks.png" % ri))

        made.append(ri)

    print("已生成 %d 排 -> %s" % (len(made), out_dir))
    print("  整排图: row_N.png")
    if marked:
        print("  标号图: row_N_marks.png（简谱区，数字上方红字为 spec 音序号）")
    # 打印一份对照表，方便标记者核对
    print()
    print("%-4s %-6s %-8s %s" % ("排", "音数", "文件名", "音序号 → note.x"))
    for ri in made:
        r = spec["rows"][ri - 1]
        notes = r.get("notes", [])
        xs = " ".join("%d:%.0f" % (i, n.get("x", 0)) for i, n in enumerate(notes, 1))
        print("  %-3d %-5d row_%d_marks.png   %s" % (ri, len(notes), ri, xs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=ROW_W)
    ap.add_argument("--no-marks", action="store_true")
    a = ap.parse_args()
    build(load_spec(a.spec), a.out, a.width, not a.no_marks)


if __name__ == "__main__":
    main()
