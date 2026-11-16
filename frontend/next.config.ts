import type { NextConfig } from "next";

const config: NextConfig = {
  // Standalone is for the Docker image, which copies `.next/standalone`. Vercel builds and
  // runs the app its own way, and the extra copy only confuses it, so it is left off there.
  output: process.env.VERCEL ? undefined : "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  // The content security policy is set per request in middleware.ts, because it carries a nonce.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          // Invitation links carry a token in the URL, so nothing may leak it to another site.
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default config;
