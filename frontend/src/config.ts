// API Configuration
export const API_CONFIG = {
  // Use environment variable if available, otherwise fallback to working backend deployment
  BASE_URL: process.env.REACT_APP_API_BASE_URL || (
    process.env.NODE_ENV === 'production' 
      ? 'https://statchat-hunxox8fc-kweku-ulzens-projects.vercel.app'
      : 'http://localhost:8000'
  )
};
