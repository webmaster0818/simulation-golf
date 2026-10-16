import { pageUrlMeta } from '../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, FACILITIES, OPEN_FACILITIES, brands, activePrefs, asOf, GENERATED_AT,
} from '../../lib/data'
import { JsonLd, breadcrumb } from '../../lib/seo'

export const metadata: Metadata = {
  title: '掲載ポリシー・掲載データについて｜出典と情報の集め方',
  description:
    'シミュレーションゴルフ・インドアゴルフの比較サイトとしての掲載ポリシーと、施設情報の集め方・出典を公開しています。口コミ・評価は掲載していません。',
  ...pageUrlMeta(`/data/`),
}

export default function DataPage() {
  const fs = OPEN_FACILITIES
  const filled = (k: (typeof fs)[number] extends never ? never : keyof (typeof fs)[number]) =>
    fs.filter((f) => f[k]).length

  const ld = [breadcrumb([{ name: 'ホーム', url: '/' }, { name: '掲載ポリシー', url: '/data/' }])]
  return (
    <main className="wrap narrow">
      <JsonLd data={ld} />
      <nav className="crumbs"><Link href="/">ホーム</Link> / 掲載ポリシー</nav>

      <section className="hero">
        <div className="kicker">Data</div>
        <h1>掲載ポリシー・掲載データについて</h1>
        <p className="lead">
          このサイトに書いてあることが、どこから来ているのかを全部書いておきます。
        </p>
      </section>

      {/* 2026-10-16 MediaXAI「fit-best.com/content-policy を参考に、シミュレーションゴルフ・インドアゴルフの比較サイトとしての表記に」 */}
      <h2>掲載ポリシー</h2>

      <h3>目的に合う一軒を、最短で見つけられるように</h3>
      <p>
        シミュレーションゴルフ・インドアゴルフは、24時間の無人店、完全個室、コーチが付くスクール、
        屋外の打ちっぱなしに弾道計測が入った練習場と、形がさまざまです。
        立地や料金だけでなく、使っている機材や「いつ・誰と・何のために打つか」で合う施設は変わります。
        エリア・ブランド・機材・こだわり条件のどこからでも探せるように、全施設を同じ項目で整理しています。
      </p>

      <h3>公式サイトの情報を、正確に、新しく</h3>
      <p>
        掲載するのは、<strong>各施設・ブランドの公式サイトに書かれている内容だけ</strong>です。
        施設ページには、取得元のURLと取得日を必ず添えています。
        チェーンの店舗一覧は定期的に取り直し、新店・閉店・オープン日の変更・料金の改定を反映しています。
        オープン前の施設は、公式サイトで開業が確認できるまで「準備中」とし、一覧には含めません。
      </p>

      <h3>口コミや点数で順位をつけません</h3>
      <p>
        <strong>口コミ・★評価・ランキングは載せていません。</strong>
        点数や順位をつけると、情報を集めやすい店が有利になり、集まっていない店が不利になります。
        このサイトは「どこに何があって、公式に何が公開されているか」を、どの施設にも同じ基準で出すところまでに留めます。
      </p>

      <h3>分からないことは、分からないと書きます</h3>
      <p>
        公式サイトで確認できなかった項目は、推測で埋めずに「公式サイトに記載なし」と表示します。
        「たぶん24時間」「たぶん個室」と書けば一覧の見栄えは良くなりますが、行ってみたら違った、が起きるからです。
      </p>
      <div className="verdict">
        <span className="tag">「記載なし」の意味</span>
        <p style={{ marginBottom: 0 }}>
          「記載なし」は「その設備が無い」という意味ではありません。
          公式サイトの店舗ページ・料金ページ・よくある質問などを確認しても、書かれていなかったという意味です。
        </p>
      </div>

      <h2>情報の集め方</h2>
      <ol className="flow">
        <li>
          <strong>公式サイトを読む</strong>
          各ブランドの店舗一覧から、店舗ごとのページ・料金ページ・設備（シミュレーター）のページ・よくある質問までを読みます。
        </li>
        <li>
          <strong>項目をそろえる</strong>
          住所・営業時間・定休日・打席数・駐車場・料金・機材を、全施設で同じ項目に整理します。
          税込・税抜などの表記は公式の書き方のまま載せます。
          「全店舗」と公式に書かれている内容（例：よくある質問の「全店年中無休」）だけは、そのブランドの全店に反映します。
        </li>
        <li>
          <strong>目で確かめて載せる</strong>
          掲載前に、ブランドごとに複数の店舗ページを開き、掲載内容と公式の記載が一致しているかを目で確認します。
        </li>
        <li>
          <strong>取り直して更新する</strong>
          公開後も公式サイトを取り直し、変わった項目を更新します。公式の記載どうしが食い違う場合（例：店舗ページと一覧で機材が違う）は、どちらとも決めずに載せません。
        </li>
      </ol>
      <p>
        弾道計測つきの練習場は、GDOが公開している「トップトレーサー・レンジ」の導入施設一覧を出典としています。
      </p>

      <h2>いま載っているもの</h2>
      <div className="tablewrap">
        <table>
          <thead><tr><th>項目</th><th>掲載数</th></tr></thead>
          <tbody>
            <tr><td>掲載施設（営業中）</td><td className="num">{fs.length}</td></tr>
            <tr><td>屋内シミュレーションゴルフ</td><td className="num">{fs.filter((f) => f.segment === 'indoor').length}</td></tr>
            <tr><td>インドアゴルフスクール（コーチ付き）</td><td className="num">{fs.filter((f) => f.segment === 'lesson').length}</td></tr>
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
              ['定休日', 'closed'], ['打席・個室', 'bays'], ['駐車場', 'parking'], ['アクセス', 'access'],
              ['料金（月会費）', 'monthly_fee'], ['計測の設備（機材）', 'equipment'],
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
        割合が低い項目は、<strong>そのチェーンが公式サイトに店舗ごとの内容を載せていない</strong>ものです
        （例：機種は「店舗により異なります」とだけ書かれている、打席数や最寄り駅の記載が無い）。
        推測で埋めていないので、この数字がそのまま実態です。
      </p>

      <h2>集めていない施設について</h2>
      <p>
        個人経営の施設や、公式サイトで店舗情報を公開していないチェーンは、まだ掲載できていません。
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
