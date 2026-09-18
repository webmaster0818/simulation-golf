import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, FACILITIES, OPEN_FACILITIES, brands, activePrefs, asOf, GENERATED_AT,
} from '../../lib/data'

export const metadata: Metadata = {
  title: '掲載データについて｜出典・集め方・載せないと決めていること',
  description:
    '当サイトが施設情報をどこから集め、何を載せ、何を載せないかを公開しています。口コミ・評価は掲載していません。',
  alternates: { canonical: `${SITE.origin}/data/` },
}

export default function DataPage() {
  const fs = OPEN_FACILITIES
  const filled = (k: (typeof fs)[number] extends never ? never : keyof (typeof fs)[number]) =>
    fs.filter((f) => f[k]).length

  return (
    <main className="wrap narrow">
      <nav className="crumbs"><Link href="/">ホーム</Link> / 掲載データについて</nav>

      <section className="hero">
        <div className="kicker">Data</div>
        <h1>掲載データについて</h1>
        <p className="lead">
          このサイトに書いてあることが、どこから来ているのかを全部書いておきます。
        </p>
      </section>

      <h2>どこから集めているか</h2>
      <p>
        施設情報は<strong>各施設・ブランドの公式サイトに掲載されている内容</strong>だけを集めています。
        施設ごとに、取得元のURLと取得日を施設ページに記載しています。
      </p>
      <p>
        弾道計測つきの練習場は、GDOが公開しているトップトレーサー・レンジの導入施設一覧を出典としています。
      </p>

      <h2>何を載せていないか</h2>
      <div className="verdict">
        <span className="tag">載せないと決めていること</span>
        <p>
          <strong>口コミ・評価（★）は載せません。</strong>
          点数や順位をつけると、集めた店が有利になり、集まっていない店が不利になります。
          このサイトは「どこに何があって、何が公開されているか」を出すところまでに留めます。
        </p>
        <p>
          <strong>公式サイトに書かれていない項目を推測で埋めません。</strong>
          営業時間・料金・設備が公開されていない施設は「公式サイトに記載なし」と表示します。
          「たぶん24時間」「たぶん個室」と書くほうが一覧としては見栄えがしますが、
          実際に行ってみたら違った、が起きます。
        </p>
        <p style={{ marginBottom: 0 }}>
          <strong>「記載なし」は「設備が無い」ではありません。</strong>
          公式サイトで確認できなかった、という意味です。
        </p>
      </div>

      <h2>いま載っているもの</h2>
      <div className="tablewrap">
        <table>
          <thead><tr><th>項目</th><th>掲載数</th></tr></thead>
          <tbody>
            <tr><td>掲載施設（営業中）</td><td className="num">{fs.length}</td></tr>
            <tr><td>屋内シミュレーションゴルフ</td><td className="num">{fs.filter((f) => f.segment === 'indoor').length}</td></tr>
            <tr><td>弾道計測つき練習場</td><td className="num">{fs.filter((f) => f.segment === 'range').length}</td></tr>
            <tr><td>オープン準備中（一覧には含めない）</td><td className="num">{FACILITIES.length - fs.length}</td></tr>
            <tr><td>掲載のある都道府県</td><td className="num">{activePrefs().length}</td></tr>
            <tr><td>ブランド</td><td className="num">{brands().length}</td></tr>
          </tbody>
        </table>
      </div>

      <h2>項目ごとの取得状況</h2>
      <p>
        公式サイトで公開されている項目はブランドによって差があります。
        「全施設で比較できる項目」と「一部しか分からない項目」を、正直に出しておきます。
      </p>
      <div className="tablewrap">
        <table>
          <thead><tr><th>項目</th><th>取得できた施設</th><th>割合</th></tr></thead>
          <tbody>
            {([
              ['住所', 'address'], ['電話番号', 'tel'], ['営業時間', 'hours'],
              ['打席・個室', 'bays'], ['駐車場', 'parking'], ['アクセス', 'access'],
              ['料金（月会費）', 'monthly_fee'],
            ] as const).map(([label, key]) => (
              <tr key={key}>
                <td>{label}</td>
                <td className="num">{filled(key)} / {fs.length}</td>
                <td className="num">{Math.round((filled(key) / fs.length) * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="source">
        料金の取得率が低いのは、多くのチェーンが<strong>店舗ごとの料金を公式サイトに載せていない</strong>ためです。
        推測で埋めていないので、この数字がそのまま実態です。
      </p>

      <h2>集めていない施設について</h2>
      <p>
        個人経営の施設や、公式サイトで店舗情報を公開していないチェーンは、まだ掲載できていません。
        また、店舗ページの内容がブラウザ上でしか表示されない作りのサイト（HTMLに住所が含まれないもの）も、
        現時点では取得していません。
      </p>

      <h2>更新</h2>
      <p>
        現在のデータは{asOf(GENERATED_AT)}のものです。
        公式サイトの内容は変わります。<strong>利用前には必ず、施設ページからリンクしている公式サイトで
        最新の内容をご確認ください。</strong>
      </p>
    </main>
  )
}
