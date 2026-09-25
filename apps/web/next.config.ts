import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  ...(process.env.KINGAWEB_STATIC_EXPORT === "true"
    ? { output: "export" as const, trailingSlash: true }
    : {}),
  transpilePackages: ["@kingaweb/design-system"],
  agentRules: false,
};
export default nextConfig;
