#!/usr/bin/env python3
"""OG画像（public/og-image.png・1200x630）。2026-10-16 明るいデザイン・ロゴ A-3・FV と同じ打席の写真。数字は入れない（古くなるため）"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent
W, H = 1200, 630; INK, DIM, LINE = (20, 33, 27), (95, 107, 98), (221, 227, 218)
EN_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"; JP_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc"; JP = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
def main():
    S = 2; im = Image.new("RGB", (W * S, H * S), (255, 255, 255))
    ph = Image.open(ROOT / "public/images/top/hero-studio.webp").convert("RGB")
    pw = int(ph.height * (600 / H)); crop = ph.crop((ph.width - pw, 0, ph.width, ph.height))
    im.paste(crop.resize((600 * S, H * S), Image.LANCZOS), ((W - 600) * S, 0))
    d = ImageDraw.Draw(im); d.rectangle([(W - 600) * S - 1, 0, (W - 600) * S, H * S], fill=LINE)
    logo = Image.open(ROOT / "public/images/logo-mark.png").convert("RGBA").resize((88 * S, 88 * S), Image.LANCZOS); im.paste(logo, (64 * S, 70 * S), logo)
    def put(xy, s, font, size, fill): d.text((xy[0] * S, xy[1] * S), s, font=ImageFont.truetype(font, size * S), fill=fill)
    put((168, 86), "SIM GOLF SEARCH", EN_BOLD, 34, INK); put((170, 128), "シミュレーションゴルフ検索", JP, 18, DIM)
    put((64, 244), "全国1,000以上の", JP_BOLD, 38, INK); put((64, 298), "シミュレーションゴルフから、", JP_BOLD, 38, INK); put((64, 352), "ベストを最短で見つける。", JP_BOLD, 38, INK)
    d.rectangle([64 * S, 428 * S, 124 * S, 431 * S], fill=(22, 163, 74))
    put((64, 456), "個室・24時間営業・駐車場・弾道計測の機材を", JP, 20, DIM); put((64, 486), "公式サイトの情報だけで比べられます", JP, 20, DIM)
    put((64, 566), "golf-simulate.com", JP, 18, DIM)
    out = ROOT / "public/og-image.png"; im.resize((W, H), Image.LANCZOS).save(out, optimize=True); print("書き出し →", out)
if __name__ == "__main__": main()
