#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OG画像（public/og-image.png・1200x630）を作る。

⚠️ **画像に施設数を入れない。** 以前は「全国468施設を…」と入れていたが、
   施設を足すたびに画像だけ古い数字のまま残った（468のまま600件・671件になっていた）。
   画像の中の数字は公開前チェックでも検出できない。数字はページ本文で出す。

  python3 scripts/make-og.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H = 1200, 630
BG, GRID = (13, 17, 15), (28, 40, 34)
INK, DIM, FAINT = (236, 238, 232), (150, 160, 152), (110, 120, 112)
TRACE = (196, 245, 66)          # サイトの --trace（弾道の軌跡）

JP_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc"
JP = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
EN_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def main() -> None:
    S = 2   # 2倍で描いて縮める（線と文字の縁をなめらかにする）
    im = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W * S, 30 * S):
        d.line([(x, 0), (x, H * S)], fill=GRID, width=1)
    for y in range(0, H * S, 30 * S):
        d.line([(0, y), (W * S, y)], fill=GRID, width=1)

    # 弾道。打ち出し点（左下）から頂点を通って右下へ落ちる放物線
    x0, y0, x1, top = 92, 542, 1135, 170
    pts = []
    for i in range(401):
        t = i / 400
        x = x0 + (x1 - x0) * t
        y = y0 - (y0 - top) * 4 * t * (1 - t)
        pts.append((x * S, y * S))
    d.line(pts, fill=TRACE, width=4 * S, joint="curve")
    d.ellipse([(x0 - 8) * S, (y0 - 8) * S, (x0 + 8) * S, (y0 + 8) * S], fill=INK)

    def put(xy, s, font, size, fill):
        d.text((xy[0] * S, xy[1] * S), s, font=ImageFont.truetype(font, size * S), fill=fill)

    put((86, 96), "SIM GOLF NAVI", EN_BOLD, 40, DIM)
    put((86, 160), "シミュレーションゴルフ ナビ", JP_BOLD, 76, INK)
    put((86, 288), "全国の施設を公式サイトの情報だけで比較", JP, 38, INK)
    put((86, 350), "個室 / 打席数 / 24時間営業 / 駐車場 / 弾道計測の機材", JP, 28, FAINT)
    put((86, 566), "golf-simulate.com", JP, 28, FAINT)

    out = ROOT / "public" / "og-image.png"
    im.resize((W, H), Image.LANCZOS).save(out, optimize=True)
    print(f"書き出し → {out}")


if __name__ == "__main__":
    main()
