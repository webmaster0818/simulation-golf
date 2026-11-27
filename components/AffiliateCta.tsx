import type { Affiliate } from '../lib/affiliate'

// 広告リンク（PR表記つき）。公式サイトへの通常リンク・出典リンクとは別に置く。
export default function AffiliateCta({ a, name }: { a: Affiliate; name: string }) {
  return (
    <p className="affiliate-cta">
      <span className="pr">PR</span>{' '}
      <a href={a.href} target="_blank" rel="sponsored nofollow noopener">{a.label}</a>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={a.pixel} width={1} height={1} alt="" style={{ border: 'none' }} />
      <br />
      <small>{name}の公式サイトへ移動します（広告リンク）。広告の有無は掲載内容に影響しません。</small>
    </p>
  )
}
