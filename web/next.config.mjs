/** @type {import('next').NextConfig} */
const config = {
  // The secured twins (/secure/*) are frame-protected against clickjacking.
  // The vulnerable pages deliberately omit this - see WEB-CLICKJACK-001.
  async headers() {
    return [
      {
        source: '/secure/:path*',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Content-Security-Policy', value: "frame-ancestors 'none'" },
        ],
      },
    ]
  },
}

export default config
