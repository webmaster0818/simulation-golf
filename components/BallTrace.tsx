'use client'
import { useEffect, useRef, useState } from 'react'

/**
 * 弾道ライン（2026-10-16 MediaXAI「スクロールすると、ボールの軌跡（弧）がページの上から下へ描かれていき、各ブロックに着地する演出」）。
 * ・.g-trace-host の中の [data-landing] の位置を測って、左の余白に弧をつなぐ
 * ・スクロール量に合わせて線を描き、ボールが線の先端を進む。着地点を通ると印が点く
 * ・余白が無い幅（スマホ・狭い画面）と「動きを減らす」設定では出さない。装飾なので aria-hidden
 */
type Geo = { d: string; w: number; h: number; marks: { x: number; y: number }[] }

export default function BallTrace() {
  const [geo, setGeo] = useState<Geo | null>(null)
  const path = useRef<SVGPathElement>(null)
  const ball = useRef<SVGCircleElement>(null)
  const svg = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const host = document.querySelector<HTMLElement>('.g-trace-host')
    if (!host) return
    const measure = () => {
      const r = host.getBoundingClientRect()
      const gutter = (r.width - 1040) / 2
      if (gutter < 70) { setGeo(null); return }
      const x = gutter / 2
      const ys = [...host.querySelectorAll<HTMLElement>('[data-landing]')].map(
        (el) => el.getBoundingClientRect().top - r.top + 70,
      )
      if (ys.length < 2) { setGeo(null); return }
      let d = `M ${x} ${ys[0]}`
      for (let i = 1; i < ys.length; i++) {
        const y0 = ys[i - 1], y1 = ys[i]
        // 打ち上げて落ちる弧。外側（左）にふくらませて、本文にかぶらないようにする
        d += ` C ${x - gutter * 0.38} ${y0 + (y1 - y0) * 0.15}, ${x - gutter * 0.38} ${y0 + (y1 - y0) * 0.7}, ${x} ${y1}`
      }
      setGeo({ d, w: r.width, h: host.offsetHeight, marks: ys.map((y) => ({ x, y })) })
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(host)
    window.addEventListener('resize', measure)
    return () => { ro.disconnect(); window.removeEventListener('resize', measure) }
  }, [])

  useEffect(() => {
    const p = path.current, b = ball.current, s = svg.current
    const host = document.querySelector<HTMLElement>('.g-trace-host')
    if (!geo || !p || !b || !s || !host) return
    const len = p.getTotalLength()
    p.style.strokeDasharray = `${len}`
    const marks = [...s.querySelectorAll<SVGGElement>('.g-trace-mark')]
    const onScroll = () => {
      const r = host.getBoundingClientRect()
      const reach = window.innerHeight * 0.62 - r.top // 画面の6割の高さまで来たところを先端にする
      // 先端の y に一番近い長さを二分探索（弧は y について単調）
      let lo = 0, hi = len
      for (let i = 0; i < 22; i++) { const m = (lo + hi) / 2; if (p.getPointAtLength(m).y < reach) lo = m; else hi = m }
      const at = Math.max(0, Math.min(len, lo))
      p.style.strokeDashoffset = `${len - at}`
      const pt = p.getPointAtLength(at)
      b.setAttribute('cx', String(pt.x)); b.setAttribute('cy', String(pt.y))
      b.style.opacity = at > 2 && at < len - 2 ? '1' : '0'
      marks.forEach((m, i) => m.classList.toggle('on', geo.marks[i].y <= pt.y + 2))
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [geo])

  if (!geo) return null
  return (
    <svg ref={svg} className="g-trace" width={geo.w} height={geo.h} viewBox={`0 0 ${geo.w} ${geo.h}`} aria-hidden="true">
      <path d={geo.d} className="g-trace-guide" />
      <path ref={path} d={geo.d} className="g-trace-line" />
      {geo.marks.map((m, i) => (
        <g key={i} className="g-trace-mark" transform={`translate(${m.x} ${m.y})`}>
          <ellipse rx="13" ry="4" cy="2" />
          <line x1="0" y1="0" x2="0" y2="-22" />
          <path d="M0 -22 L12 -18 L0 -14 Z" />
        </g>
      ))}
      <circle ref={ball} className="g-trace-ball" r="6" cx={geo.marks[0].x} cy={geo.marks[0].y} />
    </svg>
  )
}
