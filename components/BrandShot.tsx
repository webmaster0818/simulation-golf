/* eslint-disable @next/next/no-img-element */
import captures from '../data/brand-captures.json'

// ブランドの公式サイトのキャプチャ＋出典（2026-10-16 MediaXAI「各サービス名の紹介箇所は該当の公式サイトをキャプチャの上、画像掲載して」）。
// 撮影は scripts/capture-brands/run.sh（撮影元URL・日付は data/brand-captures.json）。キャプチャの無いブランドは何も出さない。
const CAP: Record<string, { name: string; captured_at: string }> = Object.fromEntries(
  (captures as { slug: string; name: string; captured_at: string }[]).map((c) => [c.slug, c]),
)
const jp = (d: string) => { const [y, m, dd] = d.split('-').map(Number); return `${y}年${m}月${dd}日` }
export const hasBrandShot = (slug: string) => !!CAP[slug]
export default function BrandShot({ slug, name, compact = false }: { slug: string; name: string; compact?: boolean }) {
  const cap = CAP[slug]
  if (!cap) return null
  if (compact) return <img className="g-thumb" src={`/images/brands/${slug}.webp`} alt={`${name} 公式サイト`} width={1280} height={800} loading="lazy" />
  return (
    <figure className="g-shot">
      <img src={`/images/brands/${slug}.webp`} alt={`${name} 公式サイトのトップページ`} width={1280} height={800} loading="lazy" />
      <figcaption>出典：{name} 公式サイト（{jp(cap.captured_at)}時点）</figcaption>
    </figure>
  )
}
