/** @type {import('next').NextConfig} */
const isGithubPages = process.env.GITHUB_PAGES === "true";
const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] || "FinanceAnalysis";

const nextConfig = {
  reactStrictMode: true,
  // Standalone for Docker; static export for GitHub Pages.
  ...(isGithubPages
    ? {
        output: "export",
        basePath: `/${repoName}`,
        assetPrefix: `/${repoName}/`,
        trailingSlash: true,
        images: { unoptimized: true }
      }
    : {
        output: "standalone"
      }),
  experimental: {
    useTypeScriptCli: true
  },
  async rewrites() {
    if (isGithubPages) {
      return [];
    }
    const backend = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backend}/api/v1/:path*`
      }
    ];
  }
};

export default nextConfig;
