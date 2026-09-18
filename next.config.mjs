/** @type {import('next').NextConfig} */
// Cloudflare Pages にローカルビルド方式で載せるため静的書き出しに固定する。
// trailingSlash: true = /facility/xxx/ の形。canonical と内部リンクも必ずスラッシュ付きで揃える。
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  trailingSlash: true,
}
export default nextConfig
