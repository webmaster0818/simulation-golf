import type { Metadata } from 'next'
import { Chakra_Petch, Zen_Kaku_Gothic_New } from 'next/font/google'
import Link from 'next/link'
import './globals.css'
import { OG_BASE, OG_IMAGE } from '../lib/meta'
import { SITE, REGIONS, PREF_SLUG, activePrefs, brands, FEATURES } from '../lib/data'

// 計測器の表示に寄せた角のある書体を英数字に、本文は読みやすい日本語ゴシックに分ける。
const tech = Chakra_Petch({
  subsets: ['latin'], weight: ['500', '700'], display: 'swap', variable: '--font-tech',
})
const jp = Zen_Kaku_Gothic_New({
  subsets: ['latin'], weight: ['400', '500', '700'], display: 'swap', variable: '--font-jp',
})

// OG画像・共通OGPは lib/meta.ts（各ページの pageUrlMeta と同じ値を使う）

export const metadata: Metadata = {
  metadataBase: new URL(SITE.origin),
  title: {
    default: `${SITE.name}｜全国のシミュレーションゴルフを公式情報で比較`,
    template: `%s｜${SITE.name}`,
  },
  description: SITE.description,
  // ⚠️ ここに canonical を置かない。置くと全ページがトップを正規URLとして宣言してしまう。
  //    （他サイトで実際に起きた事故。canonical は各ページで個別に付ける）
  // ⚠️ ここに og:url を置かない。各ページに引き継がれ、全ページの og:url が TOP になる（2026-10-12 に1152ページで発生）。
  //    og:url は canonical と一緒に各ページの pageUrlMeta() で出す。
  openGraph: OG_BASE,
  twitter: { card: 'summary_large_image', images: [OG_IMAGE] },
  alternates: { types: { 'application/xml': `${SITE.origin}/sitemap.xml` } },
  // 2026-10-16 ロゴ A-3。ブラウザがファビコンを強くキャッシュするので、ファイル名ごと変えて読み直させる
  icons: { icon: [{ url: '/favicon-20261016.png', type: 'image/png', sizes: '64x64' }], apple: '/apple-touch-icon.png?v=20261016' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const prefs = activePrefs()

  return (
    <html lang="ja" className={`${tech.variable} ${jp.variable}`}>
      <body>
        <header className="site">
          <div className="inner">
            <Link href="/" className="logo">
              <img src="/images/logo-mark.png" alt="" width={38} height={38} />
              <span className="t">SIM GOLF SEARCH<em>シミュレーションゴルフ検索</em></span>
            </Link>
            <nav>
              <Link href="/area/">エリアから探す</Link>
              <Link href="/brand/">ブランドから探す</Link>
              <Link href="/equipment/">計測機器から探す</Link>
              <Link href="/data/">掲載ポリシー</Link>
            </nav>
          </div>
        </header>

        {children}

        <footer className="site">
          <div className="wrap cols">
            <div>
              <h4>Area</h4>
              <ul>
                {REGIONS.map((r) => {
                  const has = r.prefs.filter((p) => prefs.includes(p))
                  if (!has.length) return null
                  return (
                    <li key={r.name}>
                      {has.map((p, i) => (
                        <span key={p}>
                          {i > 0 && ' / '}
                          <Link href={`/area/${PREF_SLUG[p]}/`}>{p}</Link>
                        </span>
                      ))}
                    </li>
                  )
                })}
              </ul>
            </div>
            <div>
              <h4>Brand</h4>
              <ul>
                {brands().map((b) => (
                  <li key={b.slug}>
                    <Link href={`/brand/${b.slug}/`}>{b.name}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Filter</h4>
              <ul>
                {FEATURES.map((f) => (
                  <li key={f.slug}>
                    <Link href={`/feature/${f.slug}/`}>{f.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4>About</h4>
              <ul>
                <li><Link href="/data/">掲載ポリシー</Link></li>
                <li><Link href="/equipment/">弾道計測の機器について</Link></li>
              </ul>
            </div>
          </div>
          <div className="wrap">
            <p className="note">
              掲載している施設情報は、各施設・ブランドの公式サイトで公開されている内容をもとにしています。
              施設ごとに出典URLと情報取得日を明記しています。料金・営業時間・設備は変更される場合がありますので、
              ご利用前に各施設の公式サイトにて最新情報をご確認ください。
              <br />
              当サイトでは口コミ・評価を掲載していません。公式サイトで確認できない項目は「公式サイトに記載なし」と表示しています。
            </p>
          </div>
        </footer>
      </body>
    </html>
  )
}
