import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@kingaweb/design-system"],
  agentRules: false,
};
export default nextConfig;
