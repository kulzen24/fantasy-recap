// API Configuration
export const API_CONFIG = {
  // Use environment variable if available, otherwise fallback to static Vercel URL in production
  BASE_URL: process.env.REACT_APP_API_BASE_URL || (
    process.env.NODE_ENV === 'production' 
      ? 'https://statchat-ashen.vercel.app'
      : 'http://localhost:8000'
  )
};
