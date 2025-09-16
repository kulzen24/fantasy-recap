// API Configuration
export const API_CONFIG = {
  // Use static Vercel backend in production, localhost in development
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'https://statchat-ashen.vercel.app'
    : 'http://localhost:8000'
};
