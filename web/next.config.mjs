/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",        // 纯静态导出：由后端（FastAPI）托管，运行时无需 Node
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
};
export default nextConfig;