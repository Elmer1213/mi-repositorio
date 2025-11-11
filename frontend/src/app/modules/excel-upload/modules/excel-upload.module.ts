export interface ExcelPreviewRow {
  row_number: number;
  name: string;
  email: string;
  is_valid: boolean;
  errors: string[];
}

export interface ExcelPreviewResponse {
  total_rows: number;
  preview_rows: ExcelPreviewRow[];
  columns: string[];
  has_errors: boolean;
}

export interface UploadLog {
  id: number;
  filename: string;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  error_message?: string;
}

export interface UploadProgressResponse {
  current: number;
  total: number;
  percentage: number;
  status: string;
}

export interface UploadResponse {
  message: string;
  upload_id: number;
  total_rows: number;
}

export interface ValidationResponse {
  message: string;
  filename: string;
  size_ok: boolean;
}