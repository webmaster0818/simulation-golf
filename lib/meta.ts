import type { Metadata } from 'next'
import { SITE } from './data'

// ⚠️ OG画像を差し替えたら v= を必ず上げる。/og-image.png は _headers で7日キャッシュさせており、
//    同じURLのままだと Cloudflare のエッジに古い画像が残る（2026-10-02、差し替え後も
//    独自ドメインだけ旧画像が返った。pages.dev は新しくなるので気づきにくい）。
export const OG_IMAGE = '/og-image.png?v=20261002'

/**
 * OGP の共通値（layout.tsx と各ページで共用）。
 * OGPは1枚を全ページ共通で使う。施設ごとに画像を作ると、公式から借りた写真を
 * 出典の文脈から切り離して配ることになるので、サイトの版面を出す。
 * ⚠️ ページ側で openGraph を書くと layout の openGraph は丸ごと置き換わるので、必ずこれを展開する。
 */
export const OG_BASE: NonNullable<Metadata['openGraph']> = {
  type: 'website',
  siteName: SITE.name,
  locale: 'ja_JP',
  images: [{ url: OG_IMAGE, width: 1200, height: 630, alt: SITE.name }],
}

/**
 * canonical と og:url を同じURLから組み立てる（2026-10-12）。
 * layout の openGraph.url（TOP）が全ページに引き継がれ、1152ページで og:url が TOP になっていた。
 * 使い方: { ...pageUrlMeta(`/facility/${slug}/`), title, description }
 */
export function pageUrlMeta(path: string): Pick<Metadata, 'alternates' | 'openGraph'> {
  const url = `${SITE.origin}${path}`
  return {
    alternates: { canonical: url },
    openGraph: { ...OG_BASE, url },
  }
}
