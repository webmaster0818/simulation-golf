import Link from 'next/link'
import { OFFICIAL_TABLES } from '../lib/page-official-tables'

const jpDate = (d: string) => { const [y, m, day] = d.split('-'); return `${y}年${Number(m)}月${Number(day)}日` }

/** エリア・ブランドページの「公式サイトで確認した施設情報」。データの無いページには何も出さない */
export default function OfficialTables({ pageKey }: { pageKey: string }) {
  const t = OFFICIAL_TABLES[pageKey]
  if (!t) return null
  return (
    <>
      <h2>{t.heading}</h2>
      <p>{t.intro}</p>
      {t.groups.map((g) => (
        <div key={g.name}>
          <h3>{g.slug ? <Link href={`/facility/${g.slug}/`}>{g.name}</Link> : g.name}</h3>
          <div className="tablewrap">
            <table>
              <thead><tr><th>項目</th><th>記載内容</th></tr></thead>
              <tbody>
                {g.rows.map((r) => <tr key={r.k}><td>{r.k}</td><td>{r.v}</td></tr>)}
              </tbody>
            </table>
          </div>
          <p className="source">
            出典：
            {g.sources.map((s, i) => (
              <span key={s.url}>
                {i > 0 && '／'}
                <a href={s.url} target="_blank" rel="noopener noreferrer">{s.label}</a>
              </span>
            ))}
            （{jpDate(g.checked)}に確認）。
            {g.note ?? ''}
          </p>
        </div>
      ))}
      <p className="source">料金・営業時間は変更される場合がありますので、ご利用前に公式サイトまたは施設にてご確認ください。</p>
    </>
  )
}
