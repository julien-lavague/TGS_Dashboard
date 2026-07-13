import type { NextConfig } from "next";

// In production set BACKEND_URL to the deployed backend (e.g. the Railway URL).
// Locally it falls back to the dev uvicorn server on :8000.
const backend = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
