import { OPEN_FACILITIES, activePrefs, byFeature } from '../lib/data'

// TOP のファーストビュー（2026-10-16 MediaXAI がデザイン案1「全面写真型」を選択）。
// ⚠️ 数字は facilities.json から計算する（手で書かない）。料金は表記がばらばらで「最安〇円」を言えないので出さない。
export default function TopHero() {
  const stats = [
    { k: '掲載施設（営業中）', v: OPEN_FACILITIES.length.toLocaleString(), u: '施設' },
    { k: '対応エリア', v: String(activePrefs().length), u: '都道府県' },
    { k: '24時間営業', v: byFeature('open-24h').length.toLocaleString(), u: '施設' },
    { k: '個室で打てる', v: byFeature('private-room').length.toLocaleString(), u: '施設' },
  ]
  const chips = [
    { href: '/feature/open-24h/', label: '24時間営業' },
    { href: '/feature/private-room/', label: '個室' },
    { href: '/feature/parking/', label: '駐車場' },
    { href: '/equipment/trackman/', label: 'トラックマン' },
    { href: '/equipment/toptracer/', label: 'トップトレーサー' },
  ]
  return (
    <section className="g-hero" aria-labelledby="hero-title" data-landing>
      <picture className="g-hero-photo">
        <source media="(max-width: 767px)" srcSet="/images/top/hero-studio-sp.webp" />
        <img src="/images/top/hero-studio.webp" alt="最新の設備がそろった明るいシミュレーションゴルフの打席" width={2400} height={1339} fetchPriority="high" />
      </picture>
      <div className="g-hero-copy">
        <p className="g-hero-label">公式サイトの情報だけで比べる、シミュレーションゴルフの検索サイト</p>
        <h1 id="hero-title" className="g-hero-title">
          <span><b>全国1,000以上の</b><b>シミュレーションゴルフから、</b></span>
          <span>ベストを最短で見つける。</span>
        </h1>
        <div className="g-actions">
          <a className="g-btn g-btn-lg" href="#area">エリアから探す</a>
          <a className="g-btn g-btn-lg" href="#feature">条件から探す</a>
        </div>
        <ul className="g-chips">
          {chips.map((c) => <li key={c.href}><a className="g-chip" href={c.href}>{c.label}</a></li>)}
        </ul>
      </div>
      <dl className="g-stats">
        {stats.map((s) => (
          <div key={s.k} className="g-stat"><dt>{s.k}</dt><dd><span className="g-count" data-to={s.v.replace(/,/g, '')}>{s.v}</span><span className="u">{s.u}</span></dd></div>
        ))}
      </dl>
      <p className="g-note">※ 数字は各施設の公式サイトの掲載内容から当サイトが集計したものです。写真はイメージで、特定の施設ではありません。</p>
    </section>
  )
}
