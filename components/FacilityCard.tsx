import Link from 'next/link'
import type { Facility } from '../lib/data'

/** 施設カード。
 *  ⚠️ タグは実データで判定できたものだけ出す。
 *     「公式に書いていない＝無い」ではないので、無い項目はタグを出さないだけにして、
 *     「駐車場なし」のような断定は表示しない。 */
const SEGMENT_LABEL: Record<string, string> = {
  indoor: '屋内シミュレーションゴルフ（単独店）',
  lesson: 'インドアゴルフスクール（単独店）',
  range: '弾道計測つき練習場',
}

export default function FacilityCard({ f }: { f: Facility }) {
  const hasParking = !!f.parking && !/^無|なし/.test(f.parking) && !/近隣|近く/.test(f.parking)
  const isPrivate = f.private_room === true || /個室/.test(f.bays ?? '')

  return (
    <Link href={`/facility/${f.slug}/`} className="card">
      {/* ⚠️ ブランド無し＝練習場ではない。独立の屋内施設（紀州インドアゴルフ等）に
          「弾道計測つき練習場」と出ていた（2026-10-03）。業態で出し分ける */}
      <span className="brand">{f.brand ?? SEGMENT_LABEL[f.segment] ?? '単独施設'}</span>
      <div className="nm">{f.name}</div>
      <div className="ad">{f.address ?? '住所の記載なし'}</div>
      <div className="tags">
        {f.open_24h && <span className="tag-chip on">24時間</span>}
        {isPrivate && <span className="tag-chip on">個室</span>}
        {f.bays_num ? <span className="tag-chip">{f.bays_num}打席</span> : null}
        {hasParking && <span className="tag-chip">駐車場</span>}
        {f.segment === 'range' && f.usage_fee === '無料' && (
          <span className="tag-chip on">計測無料</span>
        )}
        {f.distance_yard ? <span className="tag-chip">{f.distance_yard}ヤード</span> : null}
      </div>
    </Link>
  )
}
