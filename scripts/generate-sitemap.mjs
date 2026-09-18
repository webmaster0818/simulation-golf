// ビルド後に out/sitemap.xml と robots.txt を作る。
// ⚠️ ページを増やしたらここにも足す（全サイト共通のルール）。
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const ORIGIN = 'https://simulation-golf-deploy.pages.dev'
const today = new Date().toISOString().slice(0, 10)

const data = JSON.parse(readFileSync(join(ROOT, 'data/facilities.json'), 'utf-8'))
const facilities = data.facilities

const PREF_SLUG = JSON.parse(readFileSync(join(ROOT, 'data/pref-slug.json'), 'utf-8'))
const FEATURES = ['private-room', 'open-24h', 'parking', 'free-trace']

const prefs = [...new Set(facilities.filter((f) => f.open && f.pref).map((f) => f.pref))]
const brands = [...new Set(facilities.filter((f) => f.open && f.brand_slug).map((f) => f.brand_slug))]

const urls = [
  '/', '/area/', '/brand/', '/equipment/', '/equipment/toptracer/', '/data/',
  ...prefs.map((p) => `/area/${PREF_SLUG[p]}/`),
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
