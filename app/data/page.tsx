import { pageUrlMeta } from '../../lib/meta'
import type { Metadata } from 'next'
import Link from 'next/link'
import {
  SITE, FACILITIES, OPEN_FACILITIES, brands, activePrefs, asOf, GENERATED_AT,
} from '../../lib/data'
import { JsonLd, breadcrumb } from '../../lib/seo'

export const metadata: Metadata = {
  title: '掲載ポリシー｜掲載方針・情報の収集方法・出典',
  description:
    'SIM GOLF SEARCHの掲載ポリシーです。シミュレーションゴルフ・インドアゴルフ施設の情報の収集方法と出典について記載しています。口コミ・評価は掲載していません。',
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
        <h1>掲載ポリシー</h1>
        <p className="lead">
          当サイトの掲載方針、情報の収集方法および出典についてご説明します。
        </p>
      </section>

      {/* 2026-10-16 MediaXAI「fit-best.com/content-policy を参考に」「ビジネスライクな日本語に」 */}
      <h2>掲載ポリシー</h2>

      <h3>利用者の目的に沿った施設選びを支援します</h3>
      <p>
        シミュレーションゴルフ・インドアゴルフ施設には、24時間営業の無人店舗、完全個室型の施設、
        コーチ付きのインドアゴルフスクール、弾道計測を導入した練習場など、さまざまな形態があります。
        立地や料金に加え、導入している計測機器や利用目的によっても、適した施設は異なります。
        当サイトでは全施設の情報を共通の項目で整理し、エリア・ブランド・計測機器・設備条件から比較・検索いただけるようにしています。
      </p>

      <h3>公式情報にもとづく正確な情報提供に努めます</h3>
      <p>
        掲載情報は、<strong>各施設・ブランドの公式サイトで公開されている内容に限定</strong>しています。
        施設ページには、出典URLと情報取得日を明記しています。
        各ブランドの店舗情報は定期的に確認し、新規開業・閉店・開業日の変更・料金改定などを反映しています。
        開業前の施設は、公式サイトで開業を確認できるまで「準備中」として扱い、施設一覧には含めていません。
      </p>

      <h3>中立的な立場で情報を掲載します</h3>
      <p>
        当サイトでは、<strong>口コミ・評価点・ランキングを掲載していません。</strong>
        評価点や順位を設けると、情報の集まりやすさによって施設間に有利・不利が生じるためです。
        施設の所在地や公式に公開されている情報を、すべての施設に同一の基準で掲載することを方針としています。
      </p>

      <h3>未確認の情報は掲載しません</h3>
      <p>
        公式サイトで確認できない項目は、推測による補完を行わず「公式サイトに記載なし」と表示しています。
        推測にもとづく情報が、実際の施設の状況と異なることを避けるためです。
      </p>
      <div className="verdict">
        <span className="tag">「公式サイトに記載なし」について</span>
        <p style={{ marginBottom: 0 }}>
          「公式サイトに記載なし」は、該当する設備やサービスが存在しないことを示すものではありません。
          各施設の公式サイト（店舗ページ・料金ページ・よくある質問など）を確認した時点で、該当する記載が見当たらなかったことを示しています。
        </p>
      </div>

      <h2>情報の収集・掲載の流れ</h2>
      <ol className="flow">
        <li>
          <strong>情報の収集</strong>
          各ブランドの店舗一覧をもとに、店舗ページ・料金ページ・設備紹介ページ・よくある質問などの公式情報を収集します。
        </li>
        <li>
          <strong>情報の整理</strong>
          所在地・営業時間・定休日・打席数・駐車場・料金・計測機器などの項目を、全施設共通の形式に整理します。
          料金の税込・税抜の表記は、公式サイトの表記に準じます。
          公式サイトで全店舗共通と明記されている内容に限り、同一ブランドの全店舗に反映しています。
        </li>
        <li>
          <strong>掲載内容の確認</strong>
          掲載前に、ブランドごとに複数の店舗ページと照合し、掲載内容が公式サイトの記載と一致していることを確認します。
        </li>
        <li>
          <strong>情報の更新</strong>
          掲載後も定期的に公式サイトを確認し、変更があった項目を更新します。
          公式サイト内で記載内容が一致しない場合は、いずれの情報も掲載を控えます。
        </li>
      </ol>
      <p>
        弾道計測を導入した練習場については、株式会社ゴルフダイジェスト・オンライン（GDO）が公開する
        「トップトレーサー・レンジ」導入施設一覧を出典としています。
      </p>

      <h2>掲載状況</h2>
      <div className="tablewrap">
        <table>
          <thead><tr><th>項目</th><th>件数</th></tr></thead>
          <tbody>
            <tr><td>掲載施設（営業中）</td><td className="num">{fs.length}</td></tr>
            <tr><td>屋内シミュレーションゴルフ</td><td className="num">{fs.filter((f) => f.segment === 'indoor').length}</td></tr>
            <tr><td>インドアゴルフスクール（コーチ付き）</td><td className="num">{fs.filter((f) => f.segment === 'lesson').length}</td></tr>
            <tr><td>弾道計測を導入した練習場</td><td className="num">{fs.filter((f) => f.segment === 'range').length}</td></tr>
            <tr><td>開業準備中（施設一覧には含めていません）</td><td className="num">{FACILITIES.length - fs.length}</td></tr>
            <tr><td>掲載のある都道府県</td><td className="num">{activePrefs().length}</td></tr>
            <tr><td>ブランド</td><td className="num">{brands().length}</td></tr>
          </tbody>
        </table>
      </div>

      <h2>項目ごとの取得状況</h2>
      <p>
        公式サイトで公開されている項目は、ブランドにより異なります。項目ごとの取得状況は以下のとおりです。
      </p>
      <div className="tablewrap">
        <table>
          <thead><tr><th>項目</th><th>取得施設数</th><th>割合</th></tr></thead>
          <tbody>
            {([
              ['住所', 'address'], ['電話番号', 'tel'], ['営業時間', 'hours'],
              ['定休日', 'closed'], ['打席・個室', 'bays'], ['駐車場', 'parking'], ['アクセス', 'access'],
              ['料金（月会費）', 'monthly_fee'], ['計測機器', 'equipment'],
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
        取得率が低い項目は、<strong>公式サイトに店舗ごとの情報が掲載されていない</strong>ものです
        （例：計測機器について「店舗により異なります」とのみ記載されている場合、打席数や最寄り駅の記載がない場合）。
        推測による補完は行っていないため、上記の数値は公式サイトの公開状況を示しています。
      </p>

      <h2>掲載対象外の施設について</h2>
      <p>
        公式サイトで店舗情報を公開していない施設は、現在掲載しておりません。
      </p>

      <h2>情報の更新について</h2>
      <p>
        現在の掲載情報は{asOf(GENERATED_AT)}のものです。
        公式サイトの内容は予告なく変更される場合があります。<strong>ご利用前に、施設ページに記載の公式サイトにて
        最新情報をご確認ください。</strong>
      </p>
    </main>
  )
}
