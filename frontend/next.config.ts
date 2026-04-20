import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Include LAN IPs you use from phones / other machines (blocks cross-origin dev requests).
  allowedDevOrigins: [
    "10.0.0.126",
    "10.0.0.125",
    "10.0.0.186",
    "100.111.32.31",
    "localhost",
  ],
};

export default nextConfig;
