import { brands } from '../lib/data'
import BrandShot from './BrandShot'

// 「ブランドから探す」（公式サイトのキャプチャ＋出典つきのカード・kagi の「掲載している業者」と同じ並べ方）
export default function BrandGrid() {
  const list = brands()
  return (
    <section id="brand" className="g-section g-section-soft" aria-labelledby="brand-title" data-landing>
      <div className="wrap">
        <div className="g-head" data-reveal>
          <p className="g-eyebrow">BRANDS</p>
          <h2 id="brand-title" className="g-h2">ブランドから探す</h2>
          <p className="g-lead">掲載している{list.length}ブランドの店舗を、公式サイトの情報で比較できます</p>
        </div>
        <ul className="g-brand-grid">
          {list.map((b, i) => (
            <li key={b.slug} className="g-brand" data-reveal style={{ transitionDelay: `${(i % 4) * 60}ms` }}>
              <a href={`/brand/${b.slug}/`}>
                <BrandShot slug={b.slug} name={b.name} />
                <span className="g-brand-name">{b.name}</span>
                <span className="g-brand-n">{b.count}施設</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
