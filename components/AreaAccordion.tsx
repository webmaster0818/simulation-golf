import { REGIONS, PREF_SLUG, activePrefs, byPref, cities } from '../lib/data'

// 「エリアから探す」（2026-10-16 MediaXAI・kagi-trouble-navi.com の折りたたみ形式）。
// ・東京都は最上部の別枠に23区（＋多摩の市）を並べる。関東の中には東京都を入れない
// ・最初はすべて閉じる（<details> なので JS 無しでも開閉でき、リンクは HTML に全部出る）
// ・リンクは高さ44px以上のボタン型（スマホで押しやすく）
export default function AreaAccordion() {
  const prefs = activePrefs()
  const cs = cities()
  const cityOfPref = (p: string) => cs.filter((c) => c.pref === p)
  const tokyo = cityOfPref('東京都')
  const wards = tokyo.filter((c) => c.city.endsWith('区'))
  const tama = tokyo.filter((c) => !c.city.endsWith('区'))
  const Links = ({ items }: { items: { href: string; label: string; n: number }[] }) => (
    <ul className="g-area-links">
      {items.map((c) => <li key={c.href}><a className="g-area-link" href={c.href}>{c.label}<span>{c.n}</span></a></li>)}
    </ul>
  )
  return (
    <section id="area" className="g-section" aria-labelledby="area-title" data-landing>
      <div className="wrap narrow">
        <div className="g-head" data-reveal>
          <img className="g-head-icon" src="/images/top/icon-area.webp" alt="" width={384} height={384} loading="lazy" />
          <p className="g-eyebrow">AREA SEARCH</p>
          <h2 id="area-title" className="g-h2">エリアから探す</h2>
          <p className="g-lead">{prefs.length}都道府県の施設を、市区町村ごとに選べます</p>
        </div>
        <div className="g-accordion">
          {prefs.includes('東京都') && (
            <details className="g-acc g-acc-tokyo" data-reveal>
              <summary><span className="g-acc-name">東京都<small>23区・多摩地域</small></span><span className="g-acc-count">{byPref('東京都').length}施設</span></summary>
              <div className="g-acc-body">
                <a className="g-area-pref" href={`/area/${PREF_SLUG['東京都']}/`}>東京都の施設一覧<span>{byPref('東京都').length}施設</span></a>
                <p className="g-acc-sub">23区</p>
                <Links items={wards.map((c) => ({ href: `/area/${PREF_SLUG['東京都']}/${c.slug}/`, label: c.city, n: c.items.length }))} />
                {tama.length > 0 && (<><p className="g-acc-sub">多摩地域</p><Links items={tama.map((c) => ({ href: `/area/${PREF_SLUG['東京都']}/${c.slug}/`, label: c.city, n: c.items.length }))} /></>)}
              </div>
            </details>
          )}
          {REGIONS.map((r) => {
            const ps = r.prefs.filter((p) => prefs.includes(p) && p !== '東京都')
            if (!ps.length) return null
            const n = ps.reduce((a, p) => a + byPref(p).length, 0)
            return (
              <details key={r.name} className="g-acc" data-reveal>
                <summary><span className="g-acc-name">{r.name}</span><span className="g-acc-count">{n}施設</span></summary>
                <div className="g-acc-body g-acc-prefs">
                  {ps.map((p) => (
                    <div key={p}>
                      <a className="g-area-pref" href={`/area/${PREF_SLUG[p]}/`}>{p}<span>{byPref(p).length}施設</span></a>
                      {cityOfPref(p).length > 0 && <Links items={cityOfPref(p).map((c) => ({ href: `/area/${PREF_SLUG[p]}/${c.slug}/`, label: c.city, n: c.items.length }))} />}
                    </div>
                  ))}
                </div>
              </details>
            )
          })}
        </div>
      </div>
    </section>
  )
}
