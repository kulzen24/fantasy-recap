// API Configuration
export const API_CONFIG = {
  // TEMPORARY: Use working backend until static URL is updated with the Vercel environment fix
  BASE_URL: process.env.REACT_APP_API_BASE_URL || (
    process.env.NODE_ENV === 'production' 
      ? 'https://statchat-athftdbsf-kweku-ulzens-projects.vercel.app'
      : 'http://localhost:8000'
  )
};
