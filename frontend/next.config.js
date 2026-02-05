/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable support for CSS modules and regular CSS
  webpack: (config, { isServer }) => {
    return config;
  },
};

export default nextConfig;
