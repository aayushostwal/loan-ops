// API Types based on backend models

export interface Lender {
  id: number;
  lender_name: string;
  policy_details: Record<string, any> | null;
  processed_data: Record<string, any> | null;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  created_by: string | null;
  created_at: string;
  updated_at: string;
  original_filename: string | null;
}

export interface LenderListResponse {
  total: number;
  lenders: Lender[];
}

export interface UploadLenderResponse {
  message: string;
  lender_id: number;
  status: string;
  task_id: string | null;
}

export interface LoanMatch {
  id: number;
  lender_id: number;
  lender_name?: string | null;
  match_score: number | null;
  match_analysis: Record<string, any> | null;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoanApplication {
  id: number;
  applicant_name: string;
  applicant_email: string | null;
  applicant_phone: string | null;
  application_details: Record<string, any> | null;
  processed_data: Record<string, any> | null;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  workflow_run_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  original_filename: string | null;
  matches?: LoanMatch[];
}

export interface LoanApplicationListResponse {
  total: number;
  applications: LoanApplication[];
}

export interface UploadLoanApplicationResponse {
  message: string;
  application_id: number;
  status: string;
  workflow_run_id: string | null;
}

