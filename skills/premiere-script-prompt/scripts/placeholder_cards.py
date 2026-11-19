"""Render pass-1 placeholder text boxes as transparent PNG cards (fallback when no text MOGRT).

Usage: python placeholder_cards.py placeholders.json out_dir [--w 1080 --h 1920]
placeholders.json: [{"id": "P01", "type": "GFX", "text": "Skin cross-section ...", "seq": "Body"}, ...]
Writes <out_dir>/<seq>_<id>_<type>.png per row and prints the file list.
"""
import json, sys, os, argparse, textwrap
from PIL import Image, ImageDraw, ImageFont

# Matches Premiere marker/label colours used elsewhere in the skill.
COLOURS = {"GFX": (155, 89, 182), "BROLL": (230, 126, 34), "TOS": (241, 196, 15), "LT": (26, 188, 156)}
# Vertical anchor (fraction of frame height) per type: B-roll/GFX centre, TOS upper third, LT lower third.
ANCHOR = {"GFX": 0.42, "BROLL": 0.42, "TOS": 0.22, "LT": 0.74}

def font(size):
    for f in ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arialbd.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()

def card(row, w, h):
    t = row["type"].upper()
    col = COLOURS.get(t, (200, 200, 200))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tag_f, body_f = font(int(w * 0.040)), font(int(w * 0.044))
    margin = int(w * 0.07)
    lines = textwrap.wrap(row["text"], width=30)[:6]
    line_h = int(body_f.size * 1.3)
    box_h = int(tag_f.size * 1.6) + line_h * len(lines) + int(w * 0.06)
    top = int(h * ANCHOR.get(t, 0.42)) - box_h // 2
    box = [margin, top, w - margin, top + box_h]
    d.rounded_rectangle(box, radius=28, fill=(0, 0, 0, 170), outline=col + (255,), width=8)
    y = top + int(w * 0.03)
    d.text((margin + 36, y), f"[{t}] {row.get('id', '')}", font=tag_f, fill=col + (255,))
    y += int(tag_f.size * 1.6)
    for ln in lines:
        d.text((margin + 36, y), ln, font=body_f, fill=(255, 255, 255, 255))
        y += line_h
    return img

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("out")
    ap.add_argument("--w", type=int, default=1080); ap.add_argument("--h", type=int, default=1920)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for r in json.load(open(a.json)):
        name = f"{r.get('seq', 'Seq')}_{r['id']}_{r['type'].upper()}.png"
        card(r, a.w, a.h).save(os.path.join(a.out, name))
        print(name)
