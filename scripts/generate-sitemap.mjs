// ビルド後に out/sitemap.xml と robots.txt を作る。
// ⚠️ ページを増やしたらここにも足す（全サイト共通のルール）。
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const ORIGIN = 'https://golf-simulate.com'
const today = new Date().toISOString().slice(0, 10)

const data = JSON.parse(readFileSync(join(ROOT, 'data/facilities.json'), 'utf-8'))
const facilities = data.facilities

const PREF_SLUG = JSON.parse(readFileSync(join(ROOT, 'data/pref-slug.json'), 'utf-8'))
const FEATURES = ['private-room', 'open-24h', 'parking', 'free-trace']

const prefs = [...new Set(facilities.filter((f) => f.open && f.pref).map((f) => f.pref))]

// 市区町村ページ。⚠️ 読みの表と下限は lib/data.ts が正。ここで二重に持つと
// ずれて sitemap から漏れるので、あちらから読む（to-x-ai.com で実際に漏れた）。
const libSrc = readFileSync(join(ROOT, 'lib/data.ts'), 'utf-8')
const CITY_SLUG = Object.fromEntries(
  [...libSrc.matchAll(/'([^']+)':\s*'([a-z0-9-]+)',/g)]
    .filter(([, k]) => /[市区町村]$/.test(k) || k === 'いわき市')
    .map(([, k, v]) => [k, v]))
const CITY_MIN = Number((libSrc.match(/CITY_MIN = (\d+)/) || [])[1] || 3)
const wardOf = (f) => {
  if (!f.address || !f.pref) return null
  const rest = f.address.replace(f.pref, '')
  const m = rest.match(/^(.+?市.+?区)/) || rest.match(/^(.+?[市区町村])/)
  return m ? m[1] : null
}
const cityCount = new Map()
for (const f of facilities.filter((x) => x.open)) {
  const c = wardOf(f)
  if (!c || !f.pref) continue
  const k = `${f.pref}\u0000${c}`
  cityCount.set(k, (cityCount.get(k) ?? 0) + 1)
}
const cityUrls = [...cityCount.entries()]
  .filter(([k, n]) => n >= CITY_MIN && CITY_SLUG[k.split('\u0000')[1]])
  .map(([k]) => {
    const [pref, city] = k.split('\u0000')
    return `/area/${PREF_SLUG[pref]}/${CITY_SLUG[city]}/`
  })
const missing = [...cityCount.entries()]
  .filter(([k, n]) => n >= CITY_MIN && !CITY_SLUG[k.split('\u0000')[1]])
if (missing.length) {
  console.log(`  🚨 読みの表に無い市区町村 ${missing.length}件 → lib/data.ts の CITY_SLUG に追加する`)
  for (const [k, n] of missing) console.log('     ', k.replace('\u0000', ' '), n)
}
const brands = [...new Set(facilities.filter((f) => f.open && f.brand_slug).map((f) => f.brand_slug))]

const urls = [
  '/', '/area/', '/brand/', '/equipment/', '/equipment/toptracer/', '/data/',
  ...prefs.map((p) => `/area/${PREF_SLUG[p]}/`),
  ...cityUrls,
  ...brands.map((b) => `/brand/${b}/`),
  ...FEATURES.map((f) => `/feature/${f}/`),
  ...facilities.map((f) => `/facility/${f.slug}/`),
]

const xml =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  urls.map((u) => `  <url><loc>${ORIGIN}${u}</loc><lastmod>${today}</lastmod></url>`).join('\n') +
  '\n</urlset>\n'

writeFileSync(join(ROOT, 'out/sitemap.xml'), xml)
writeFileSync(
  join(ROOT, 'out/robots.txt'),
  `User-agent: *\nAllow: /\n\nSitemap: ${ORIGIN}/sitemap.xml\n`
)
console.log(`sitemap.xml: ${urls.length} URL`)

// 404 は not-found.tsx に metadata を書いても App Router では効かない（ルートlayoutの
// 既定タイトルのまま＝トップと重複する）。noindex なので実害は無いが、
// レポートで毎回「title重複1件」として出てくるのでここで書き換える。
for (const f of ['out/404.html', 'out/404/index.html']) {
  const p = join(ROOT, f)
  if (!existsSync(p)) continue
  let h = readFileSync(p, 'utf8')
  h = h.replace(/<title>[^<]*<\/title>/, '<title>ページが見つかりません｜シミュレーションゴルフ ナビ</title>')
  writeFileSync(p, h)
}
