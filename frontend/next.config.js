/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export for Electron
  output: process.env.BUILD_ELECTRON === 'true' ? 'export' : undefined,
  // Configure trailing slash behavior (only for Electron builds)
  trailingSlash: process.env.BUILD_ELECTRON === 'true' ? true : false,
  // Disable image optimization for static export
  images: {
    unoptimized: process.env.BUILD_ELECTRON === 'true' ? true : false,
  },
  // Enable support for CSS modules and regular CSS
  webpack: (config, { isServer }) => {
    return config;
  },
};

export default nextConfig;
