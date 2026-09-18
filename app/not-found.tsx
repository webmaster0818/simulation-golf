import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="wrap narrow">
      <section className="hero">
        <div className="kicker">404</div>
        <h1>ページが見つかりません</h1>
        <p className="lead">
          URLが変わったか、掲載を取りやめた施設のページかもしれません。
        </p>
      </section>
      <div className="chips">
        <Link href="/">ホーム</Link>
        <Link href="/area/">エリアから探す</Link>
        <Link href="/brand/">ブランドから探す</Link>
        <Link href="/equipment/">機材から探す</Link>
      </div>
    </main>
  )
}
