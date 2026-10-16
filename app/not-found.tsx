import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="wrap narrow">
      <section className="hero">
        <div className="kicker">404</div>
        <h1>ページが見つかりません</h1>
        <p className="lead">
          URLが変更されたか、掲載を終了した施設のページである可能性があります。
        </p>
      </section>
      <div className="chips">
        <Link href="/">ホーム</Link>
        <Link href="/area/">エリアから探す</Link>
        <Link href="/brand/">ブランドから探す</Link>
        <Link href="/equipment/">計測機器から探す</Link>
      </div>
    </main>
  )
}
