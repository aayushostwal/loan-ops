import axios, { AxiosError } from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config';
import type {
  Lender,
  LenderListResponse,
  UploadLenderResponse,
  LoanApplication,
  LoanApplicationListResponse,
  UploadLoanApplicationResponse,
  LoanMatch,
} from '../types';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handler
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail: string }>;
    return axiosError.response?.data?.detail || axiosError.message || 'An error occurred';
  }
  return 'An unexpected error occurred';
};

// Lender API
export const lenderApi = {
  /**
   * Get list of all lenders
   */
  list: async (params?: {
    status_filter?: string;
    limit?: number;
    offset?: number;
  }): Promise<LenderListResponse> => {
    const response = await apiClient.get<LenderListResponse>(
      API_ENDPOINTS.lenders.list,
      { params }
    );
    return response.data;
  },

  /**
   * Get a single lender by ID
   */
  get: async (id: number): Promise<Lender> => {
    const response = await apiClient.get<Lender>(API_ENDPOINTS.lenders.get(id));
    return response.data;
  },

  /**
   * Upload a lender PDF document
   */
  upload: async (data: {
    file: File;
    lender_name: string;
    policy_details?: string;
    created_by?: string;
  }): Promise<UploadLenderResponse> => {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('lender_name', data.lender_name);
    if (data.policy_details) {
      formData.append('policy_details', data.policy_details);
    }
    if (data.created_by) {
      formData.append('created_by', data.created_by);
    }

    const response = await apiClient.post<UploadLenderResponse>(
      API_ENDPOINTS.lenders.upload,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Delete a lender
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.lenders.delete(id));
  },
};

// Loan Application API
export const loanApplicationApi = {
  /**
   * Get list of all loan applications
   */
  list: async (params?: {
    status_filter?: string;
    limit?: number;
    offset?: number;
  }): Promise<LoanApplicationListResponse> => {
    const response = await apiClient.get<LoanApplicationListResponse>(
      API_ENDPOINTS.loanApplications.list,
      { params }
    );
    return response.data;
  },

  /**
   * Get a single loan application by ID
   */
  get: async (id: number, includeMatches = true): Promise<LoanApplication> => {
    const response = await apiClient.get<LoanApplication>(
      API_ENDPOINTS.loanApplications.get(id),
      { params: { include_matches: includeMatches } }
    );
    return response.data;
  },

  /**
   * Upload a loan application PDF document
   */
  upload: async (data: {
    file: File;
    applicant_name: string;
    applicant_email?: string;
    applicant_phone?: string;
    application_details?: string;
    created_by?: string;
  }): Promise<UploadLoanApplicationResponse> => {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('applicant_name', data.applicant_name);
    if (data.applicant_email) {
      formData.append('applicant_email', data.applicant_email);
    }
    if (data.applicant_phone) {
      formData.append('applicant_phone', data.applicant_phone);
    }
    if (data.application_details) {
      formData.append('application_details', data.application_details);
    }
    if (data.created_by) {
      formData.append('created_by', data.created_by);
    }

    const response = await apiClient.post<UploadLoanApplicationResponse>(
      API_ENDPOINTS.loanApplications.upload,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Get matches for a loan application
   */
  getMatches: async (
    applicationId: number,
    params?: {
      status_filter?: string;
      min_score?: number;
    }
  ): Promise<LoanMatch[]> => {
    const response = await apiClient.get<LoanMatch[]>(
      API_ENDPOINTS.loanApplications.matches(applicationId),
      { params }
    );
    return response.data;
  },

  /**
   * Delete a loan application
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.loanApplications.delete(id));
  },
};

