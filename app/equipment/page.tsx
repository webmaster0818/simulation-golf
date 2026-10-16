import { pageUrlMeta } from '../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import { SITE, OPEN_FACILITIES, brands, asOf, GENERATED_AT } from '../../lib/data'
import { JsonLd, breadcrumb } from '../../lib/seo'

export const metadata: Metadata = {
  title: '計測機器から探す｜シミュレーションゴルフの弾道計測方式',
  description:
    'シミュレーションゴルフで使われる弾道計測の方式と、公式サイトで計測機器を確認できた施設をご紹介します。トラックマン・トップトレーサーの導入施設一覧も掲載しています。',
  ...pageUrlMeta(`/equipment/`),
}

export default function EquipmentIndex() {
  const trace = OPEN_FACILITIES.filter((f) => f.equipment === 'トップトレーサー・レンジ')
  // 表記ゆれ（トラックマン4 / TRACKMAN RANGE 等）があるので部分一致で数える
  const tm = OPEN_FACILITIES.filter((f) => !!f.equipment && /トラックマン|TRACKMAN|TrackMan/i.test(f.equipment))
  const free = trace.filter((f) => f.usage_fee === '無料')
  // 2026-10-16 店舗ページの取り直しで機種名が分かる施設が増えた（以前は「トップトレーサーだけ」と書いていた）
  const indoorAll = OPEN_FACILITIES.filter((f) => f.segment !== 'range')
  const withEquip = indoorAll.filter((f) => !!f.equipment)
  const noEquipBrands = brands().filter((b) => !OPEN_FACILITIES.some((f) => f.brand_slug === b.slug && !!f.equipment))

  const ld = [breadcrumb([{ name: 'ホーム', url: '/' }, { name: '計測機器から探す', url: '/equipment/' }])]
  return (
    <main className="wrap">
      <JsonLd data={ld} />
      <nav className="crumbs"><Link href="/">ホーム</Link> / 計測機器から探す</nav>

      <section className="hero">
        <div className="kicker">Equipment</div>
        <h1>計測機器から探す</h1>
        <p className="lead">
          シミュレーションゴルフの使い心地は、画面の映像よりも、<strong>打球のどの数値を計測しているか</strong>によって異なります。
          このページでは、弾道計測の方式の違いと、公式サイトで計測機器を確認できた施設についてご紹介します。
        </p>
      </section>

      <div className="verdict">
        <span className="tag">計測機器の掲載状況</span>
        <p>
          屋内施設・インドアゴルフスクール{indoorAll.length.toLocaleString()}件のうち、
          <strong>{withEquip.length}件</strong>は公式サイトで計測機器の機種名を確認できたため、施設ページに掲載しています。
          屋外の練習場は、トップトレーサー・レンジの導入施設{trace.length}件を掲載しています。
        </p>
        <p style={{ marginBottom: 0 }}>
          残りの{indoorAll.length - withEquip.length}件は、公式サイトに機種名の記載がない、または「店舗により異なります」とのみ記載されているため、
          機種を掲載していません。当サイトでは<strong>機種の推測による掲載は行っていません</strong>。
          計測機器を重視される場合は、施設ページに記載の公式サイトにてご確認ください。
        </p>
      </div>

      <h2>計測方式の違い</h2>
      <p>
        弾道計測の方式は、大きく2種類に分けられます。方式により計測できる項目が異なり、優劣を示すものではありません。
      </p>
      <div className="tablewrap">
        <table>
          <thead>
            <tr><th>方式</th><th>計測の仕組み</th><th>主な特長</th><th>主な設置場所</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>カメラ式</td>
              <td>複数のカメラでボールとクラブヘッドの動きを撮影し、弾道を算出する</td>
              <td>実際に飛んだ打球の軌跡を追跡できる</td>
              <td>屋外練習場の打席上部</td>
            </tr>
            <tr>
              <td>レーダー式</td>
              <td>電波（レーダー）でボールの速度・回転を計測する</td>
              <td>ヘッドスピードやスピン量など、目視できない数値の計測</td>
              <td>打席の後方（屋内の限られた空間でも使用可能）</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="source">
        屋内施設では打球がすぐにネットやスクリーンに当たるため、飛距離は計測した初速・打ち出し角・回転数から算出した値を表示しています。
        実際の飛距離を計測しているわけではない点が、弾道計測を導入した屋外練習場との大きな違いです。
      </p>

      <h2>トップトレーサー・レンジ（{trace.length}施設）</h2>
      <p>
        屋外練習場の打席に設置され、打球の軌跡を画面上に表示する設備です。
        ゴルフ中継で弾道に線が表示される技術と同様の仕組みを、練習場の打席で利用できます。
        このうち<strong>{free.length}施設は、計測機能を無料で利用できる</strong>と公表しています
        （打席料・ボール代は別途必要です）。
      </p>
      <p>
        <Link href="/equipment/toptracer/">
          トップトレーサー導入施設の一覧を見る（{trace.length}件）
        </Link>
      </p>

      <h2>トラックマン（{tm.length}件）</h2>
      <p>
        レーダーで打球を追跡して計測する機器です。屋内の個室型施設と、屋外練習場の両方に導入されています。
        <strong>トラックマンは全国の導入施設一覧が公表されていない</strong>ため、
        当サイトが各施設の公式サイトで導入を確認できた施設のみを掲載しています。
      </p>
      <p>
        <Link href="/equipment/trackman/">
          トラックマン導入施設の一覧を見る（{tm.length}件）
        </Link>
      </p>

      {noEquipBrands.length > 0 && (<>
      <h2>機種が公開されていないブランド</h2>
      <p>
        以下のブランドは、公式サイトに機種名の記載がないため、機種を掲載していません
        （「最新シミュレーター完備」などの記載のみ、または「店舗により異なります」との記載）。
      </p>
      <div className="chips">
        {noEquipBrands.map((b) => (
          <Link key={b.slug} href={`/brand/${b.slug}/`}>{b.name}</Link>
        ))}
      </div>
      </>)}
      <p className="source">
        {asOf(GENERATED_AT)}で各公式サイトを確認した内容です。
        公式サイトで機種が公開された場合は、出典を明記のうえ追加します。
      </p>
    </main>
  )
}
