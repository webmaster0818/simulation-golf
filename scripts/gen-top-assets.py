#!/usr/bin/env python3
"""TOP 刷新用の画像（2026-10-16 MediaXAI がファーストビュー案1・ロゴ A-3 を選択）→ design-proposals/assets/
アイコンは「白地に深緑の線画・大きめ」。色は使わない（MediaXAI 指示）。"""
import base64, json, urllib.request, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("g", Path(__file__).parent / "gen-design-proposals.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
OUT = Path(__file__).resolve().parent.parent / "design-proposals" / "assets"; OUT.mkdir(parents=True, exist_ok=True)
HERO = ("Photorealistic wide architectural photograph, 16:9, of a beautiful brand-new premium indoor simulation golf studio in Japan: a huge bright "
        "high-definition simulator screen showing a sunny green golf course, a premium hitting mat and turf, a modern launch monitor on the floor, "
        "warm and bright architectural lighting with indirect ceiling lights, clean light wood and white interior, very inviting atmosphere. "
        "One golfer seen from behind mid-swing on the right side. The left 45% of the frame is calm, softly lit, uncluttered white wall and floor "
        "(space for text). No text, no logos, no watermark, high resolution, sharp.")
ICON = ("Single large icon, monochrome line art in deep green-black #14211b on pure white, consistent medium stroke weight, rounded line caps, "
        "simple geometric, centered with generous margin, crisp vector-like edges, no fill colors, no shadows, no text. Subject: ")
ICONS = {
  "icon-private": "a private room door with a golfer silhouette inside a small framed room",
  "icon-24h": "a clock face with a small golf flag, representing open 24 hours",
  "icon-parking": "a car next to a parking sign letter P",
  "icon-trace": "a golf ball flight trace arc rising from a ball on a tee, representing free launch monitor tracking",
  "icon-area": "a folded map with a location pin",
  "icon-brand": "a storefront building with an awning and a golf flag",
  "icon-equipment": "a launch monitor device on the floor beside a golf ball on a mat",
}
def gen(name, prompt, aspect):
    out = OUT / f"{name}.png"
    if out.exists(): print("skip", name); return
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect, "imageSize": "2K"}}}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{g.MODEL}:generateContent?key={g.key()}"
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}), timeout=240) as r:
        d = json.loads(r.read())
    for p in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in p: out.write_bytes(base64.b64decode(p["inlineData"]["data"])); print("ok", name); return
gen("hero-studio", HERO, "16:9")
for n, s in ICONS.items(): gen(n, ICON + s, "1:1")
