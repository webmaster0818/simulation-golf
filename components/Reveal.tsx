'use client'
import { useEffect } from 'react'

// スクロールに合わせて data-reveal の要素を少しずつ出す。JS が動かない・動きを減らす設定の人には最初から全部見せる
export default function Reveal() {
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return
    document.documentElement.classList.add('g-js')
    const io = new IntersectionObserver((es) => {
      for (const e of es) if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target) }
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 })
    document.querySelectorAll('[data-reveal]').forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])
  return null
}
