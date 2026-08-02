/** @type {import('next').NextConfig} */
const isGithubPages = process.env.GITHUB_PAGES === "true";
const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] || "FinanceAnalysis";

const nextConfig = {
  reactStrictMode: true,
  experimental: {
    useTypeScriptCli: true
  }
};

if (isGithubPages) {
  nextConfig.output = "export";
  nextConfig.basePath = `/${repoName}`;
  nextConfig.assetPrefix = `/${repoName}/`;
  nextConfig.trailingSlash = true;
  nextConfig.images = { unoptimized: true };
} else {
  nextConfig.output = "standalone";
  nextConfig.rewrites = async () => {
    const backend = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backend}/api/v1/:path*`
      }
    ];
  };
}

export default nextConfig;
