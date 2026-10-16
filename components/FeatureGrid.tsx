import { byFeature } from '../lib/data'

// 「条件から探す」（大きい線画アイコン・色は使わない・ボタンの帯は全部同じ色＝MediaXAI 指示）
const ITEMS = [
  { href: '/feature/private-room/', icon: 'icon-private', label: '個室で打てる', feature: 'private-room' },
  { href: '/feature/open-24h/', icon: 'icon-24h', label: '24時間営業', feature: 'open-24h' },
  { href: '/feature/parking/', icon: 'icon-parking', label: '駐車場あり', feature: 'parking' },
  { href: '/feature/free-trace/', icon: 'icon-trace', label: '弾道計測が無料', feature: 'free-trace' },
  { href: '/equipment/', icon: 'icon-equipment', label: '機材から探す', note: 'トラックマン・トップトレーサー' },
  { href: '/brand/', icon: 'icon-brand', label: 'ブランドから探す', note: '公式サイトの画像つき' },
]
export default function FeatureGrid() {
  return (
    <section id="feature" className="g-section g-section-soft" aria-labelledby="feature-title" data-landing>
      <div className="wrap">
        <div className="g-head" data-reveal>
          <p className="g-eyebrow">FILTER</p>
          <h2 id="feature-title" className="g-h2">条件から探す</h2>
          <p className="g-lead">打ちたい環境を選んでください。公式サイトに記載のある施設だけを集めています。</p>
        </div>
        <ul className="g-grid3">
          {ITEMS.map((it, i) => (
            <li key={it.href} data-reveal style={{ transitionDelay: `${(i % 3) * 80}ms` }}>
              <a className="g-card" href={it.href}>
                <span className="g-card-body">
                  <img src={`/images/top/${it.icon}.webp`} alt="" width={384} height={384} loading="lazy" />
                  <span className="g-card-note">{it.feature ? `${byFeature(it.feature).length.toLocaleString()}施設` : it.note}</span>
                </span>
                <span className="g-card-label">{it.label}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
