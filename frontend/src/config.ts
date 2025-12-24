// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Lender endpoints
  lenders: {
    list: '/api/lenders/',
    get: (id: number) => `/api/lenders/${id}`,
    upload: '/api/lenders/upload',
    delete: (id: number) => `/api/lenders/${id}`,
  },
  // Loan Application endpoints
  loanApplications: {
    list: '/api/loan-applications/',
    get: (id: number) => `/api/loan-applications/${id}`,
    upload: '/api/loan-applications/upload',
    delete: (id: number) => `/api/loan-applications/${id}`,
    matches: (id: number) => `/api/loan-applications/${id}/matches`,
  },
} as const;

