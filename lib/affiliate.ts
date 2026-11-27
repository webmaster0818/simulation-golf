// アフィリエイト（2026-11-27〜）。ASP 提供のコードのまま使う（クリックURLと計測画像は対で使う・文言は変えない）。
// レントラックス（サイト 393472）の承認案件だけ。ほかのブランドは公式サイトへの通常リンクのまま。
export type Affiliate = { href: string; label: string; pixel: string; asp: string }

export const AFFILIATES: Record<string, Affiliate> = {
  // HYPERION（product 11160・テキスト1 → https://hyperion-golf.com/）
  hyperion: {
    href: 'https://www.rentracks.jp/adx/r.html?idx=0.72174.393472.7884.11160&dna=134766',
    label: '【HYPERION（ヒューペリオン）】',
    pixel: 'https://www.rentracks.jp/adx/p.gifx?idx=0.72174.393472.7884.11160&dna=134766',
    asp: 'rentracks',
  },
  // Your Golf Space（product 16375・テキスト1 → https://yourgolfspace.jp/）
  yourgolfspace: {
    href: 'https://www.rentracks.jp/adx/r.html?idx=0.72174.393472.11487.16375&dna=183677',
    label: 'Your Golf Space（ユアゴルフスペース）',
    pixel: 'https://www.rentracks.jp/adx/p.gifx?idx=0.72174.393472.11487.16375&dna=183677',
    asp: 'rentracks',
  },
}

export const affiliateFor = (brandSlug?: string | null): Affiliate | undefined =>
  brandSlug ? AFFILIATES[brandSlug] : undefined
