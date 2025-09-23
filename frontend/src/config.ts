// API Configuration
export const API_CONFIG = {
  // TEMPORARY: Use working backend deployment until static URL is updated
  BASE_URL: process.env.REACT_APP_API_BASE_URL || (
    process.env.NODE_ENV === 'production' 
      ? 'https://statchat-4m9blnewh-kweku-ulzens-projects.vercel.app'
      : 'http://localhost:8000'
  )
};
