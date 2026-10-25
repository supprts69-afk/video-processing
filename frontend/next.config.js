// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // API কলগুলো যেন একই ডোমেইনে হয়, তাই API URL আলাদা করে দেওয়ার দরকার নেই
  env: {
    NEXT_PUBLIC_MOTHER_API_URL: '', 
  }
}

module.exports = nextConfig
