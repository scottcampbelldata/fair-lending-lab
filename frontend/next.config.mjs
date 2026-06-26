/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static HTML export, no Node runtime at request time. All data is fetched
  // client side from NEXT_PUBLIC_API_BASE. `next build` emits to ./out, which
  // is what gets uploaded to Cloudflare Pages.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  distDir: process.env.NEXT_DIST_DIR || ".next",
  reactStrictMode: true,
};

export default nextConfig;
