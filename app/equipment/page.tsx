import type { Metadata } from 'next'
import Link from 'next/link'
import { SITE, OPEN_FACILITIES, brands, asOf, GENERATED_AT } from '../../lib/data'

export const metadata: Metadata = {
  title: '弾道計測の機材から探す｜シミュレーションゴルフの計測方式',
  description:
    'シミュレーションゴルフで使われる弾道計測の方式と、どの施設がどの機材を使っているかを整理しました。施設ごとに機材名が公開されているのは、現状トップトレーサー導入施設に限られます。',
  alternates: { canonical: `${SITE.origin}/equipment/` },
}

export default function EquipmentIndex() {
  const trace = OPEN_FACILITIES.filter((f) => f.equipment === 'トップトレーサー・レンジ')
  const free = trace.filter((f) => f.usage_fee === '無料')
  const noEquip = OPEN_FACILITIES.filter((f) => f.segment === 'indoor' && !f.equipment)

  return (
    <main className="wrap">
      <nav className="crumbs"><Link href="/">ホーム</Link> / 機材から探す</nav>

      <section className="hero">
        <div className="kicker">Equipment</div>
        <h1>弾道計測の機材から探す</h1>
        <p className="lead">
          シミュレーションゴルフは「画面にコースが映る」ことより、
          <strong>打った球の何を測っているか</strong>で体験が変わります。
          ここでは計測方式の違いと、施設ごとに機材が分かるものを整理しています。
        </p>
      </section>

      <div className="verdict">
        <span className="tag">先に結論</span>
        <p>
          施設ごとにどの機材が入っているかを公式サイトで公開しているのは、
          今のところ<strong>トップトレーサー導入施設の{trace.length}件だけ</strong>です。
        </p>
        <p style={{ marginBottom: 0 }}>
          屋内チェーン{noEquip.length}件は、公式サイトに「最新シミュレーター」とだけ書かれており、
          機種名が出ていません。当サイトでは<strong>機種を推測して載せていません</strong>。
          機材を重視する場合は、施設ページの公式サイトリンクから直接ご確認ください。
        </p>
      </div>

      <h2>計測方式の違い</h2>
      <p>
        弾道計測には大きく2つの考え方があります。どちらが優れているかではなく、測れるものが違います。
      </p>
      <div className="tablewrap">
        <table>
          <thead>
            <tr><th>方式</th><th>測り方</th><th>得意なこと</th><th>置かれている場所</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>カメラ式</td>
              <td>複数のカメラで、ボールとクラブヘッドの動きを撮って計算する</td>
              <td>実際に飛んだ球の軌跡をそのまま追える</td>
              <td>屋外の打席上部（練習場に多い）</td>
            </tr>
            <tr>
              <td>レーダー式</td>
              <td>電波を当てて、ボールの速度・回転を測る</td>
              <td>ヘッドスピードやスピン量など、目で見えない数値</td>
              <td>打席の後方・屋内の限られた距離でも使える</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="source">
        屋内施設は打った球がすぐネットに当たるため、飛距離は測った初速・打ち出し角・回転から
        計算して表示しています。「実際に何ヤード飛んだか」を見ているわけではない点は、
        屋外の計測つき練習場との大きな違いです。
      </p>

      <h2>トップトレーサー・レンジ（{trace.length}施設）</h2>
      <p>
        屋外の練習場の打席に取り付けられ、打った球の軌跡を画面に線で出す設備です。
        テレビのゴルフ中継で弾道に線が引かれるのと同じ仕組みが、練習場の打席で使えます。
        <strong>{free.length}施設は、この計測を無料で使える</strong>と公表しています
        （通常の打席料・ボール代は別途かかります）。
      </p>
      <p>
        <Link href="/equipment/toptracer/">
          トップトレーサー導入施設の一覧を見る（{trace.length}件）
        </Link>
      </p>

      <h2>機種が公開されていないブランド</h2>
      <p>
        以下のブランドは、店舗ページに機種名の記載がありません。
        「最新のシミュレーターを完備」といった表現はありますが、機種は特定できませんでした。
      </p>
      <div className="chips">
        {brands().map((b) => (
          <Link key={b.slug} href={`/brand/${b.slug}/`}>{b.name}</Link>
        ))}
      </div>
      <p className="source">
        {asOf(GENERATED_AT)}に各公式サイトを確認した時点の状況です。
        今後、公式サイトで機種が公開された場合は、出典つきで追加します。
      </p>
    </main>
  )
}
