# -*- coding: utf-8 -*-
import json, os
from PIL import Image

MAJOR = [0, 2, 4, 5, 7, 9, 11]
NM = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]

# Determine which notes are harmonics (泛音) based on score structure
def is_harmonic_note(ri, ni):
    # ri is 0-indexed row, ni is 0-indexed note in row
    if ri == 0: return True # Row 1 all harmonics
    if ri == 1: return ni in (0,1,2,3,4,5,10) # Row 2 M1 & M3 harmonics
    if ri == 2: return False # Row 3 stopped/open
    if ri == 3: return ni in (0,1,2,3,4,5) # Row 4 M1 harmonics
    if ri == 4: return ni >= 1 # Row 5 M2 & M3 harmonics
    if ri == 5: return True # Row 6 all harmonics
    if ri == 6: return True # Row 7 all harmonics
    if ri == 7: return False # Row 8 stopped/open
    if ri == 8: return False # Row 9 stopped/open
    if ri == 9: return ni >= 6 # Row 10 M3 harmonics
    if ri == 10: return False # Row 11 stopped/open
    if ri == 11: return False # Row 12 stopped/open
    if ri == 12: return 1 <= ni <= 6 # Row 13 M2 harmonics
    if ri == 13: return ni >= 5 # Row 14 M3 harmonics
    if ri == 14: return True # Row 15 all harmonics
    return False

def build_baisuzhen(scratch):
    spec = json.load(open(os.path.join(scratch, 'baisuzhen-argon-spec.json'), encoding='utf-8'))
    b64_rows = json.load(open(os.path.join(scratch, 'my_rows_b64.json'), encoding='utf-8'))
    rows_meta = []
    cells = []
    for ri, r in enumerate(spec['rows']):
        im = Image.open(os.path.join(scratch, 'my_rows', f'row_{ri+1}.png'))
        rows_meta.append({
            'w': im.width,
            'h': im.height,
            'bpm': r.get('bpm', 60),
            'count': len(r['notes'])
        })
        for ni, n in enumerate(r['notes']):
            rest = 1 if n.get('rest') else 0
            p_strs = [] if rest else [str(x) for x in n['p']]
            pcs = [MAJOR[int(x) - 1] % 12 for x in p_strs]
            harm = 1 if is_harmonic_note(ri, ni) else 0
            is_chord = len(p_strs) >= 2
            base_x = round(n['x'], 2)
            w = 3.80 if is_chord else 3.20
            adj_x = round(base_x - (w - 3.13) / 2, 2)
            cells.append({
                'r': ri,
                'ni': ni,
                'p': p_strs,
                'pcs': pcs,
                'x': adj_x,
                'w': w,
                'd': n['d'],
                'rest': rest,
                'harm': harm
            })
    return b64_rows, rows_meta, cells

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", ".agents", "skills", "guqin-score-page", "templates", "page.template.html",
)


def load_template():
    """读取 skill 的页面模板（唯一权威源）。"""
    with open(os.path.normpath(TEMPLATE_PATH), encoding="utf-8") as f:
        return f.read()


def fill_template(tpl, title, subtitle, nm=None):
    """用占位符填充模板，取代脆弱的字符串替换。"""
    rep = {"@@TITLE@@": title, "@@SUBTITLE@@": subtitle}
    if nm is not None:
        rep["@@NM@@"] = json.dumps(nm, ensure_ascii=False)
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    return tpl


if __name__ == "__main__":
    scratch = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "青城山下白素贞"))
    b64_rows, rows_meta, cells = build_baisuzhen(scratch)
    tpl = fill_template(
        load_template(),
        title="青城山下白素贞",
        subtitle="1 = C 正调定弦（一至七弦：1 2 4 5 6 1 2） · 2/4 拍 · 2800px 无损矢量级超清修复版",
        nm=NM,
    )
    out_html = (tpl
        .replace("@@IMGS@@", json.dumps(b64_rows))
        .replace("@@ROWS@@", json.dumps(rows_meta))
        .replace("@@CELLS@@", json.dumps(cells, ensure_ascii=False))
    )
    out_path = os.path.join(scratch, '古琴跟谱 · 青城山下白素贞_agron_my.html')
    open(out_path, 'w', encoding='utf-8').write(out_html)
    print('Generated:', out_path, os.path.getsize(out_path) // 1024, 'KB')
