import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Strict Mode remounts break @hello-pangea/dnd drag sensors in Next.js.
  reactStrictMode: false,
};

export default nextConfig;
