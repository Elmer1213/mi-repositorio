//Cada fila del preview del Excel
export interface ExcelPreviewRow {
  row_number?: number;
  name?: string;
  email?: string;
  [key: string]: any;
  errors?: string[];
  is_valid?: boolean;
  
}

//Respuesta del preview del Excel
export interface ExcelPreviewResponse {
  total_rows: number;
  has_errors: boolean;
  rows: ExcelPreviewRow[];
  private_rows?: ExcelPreviewRow[];
}

//Log de cargas
export interface UploadLog {
  id: number;
  filename: string;
  uploaded_at: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  total_rows?: number;
  successful_rows?: number;
  failed_rows?: number;
  error_message?: string;
  uploaded_by?: string;
}

//Respuesta al subir Excel (backend -> frontend)
export interface UploadResponse {
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  message?: string;
}

//Respuesta de validación de archivo
export interface ValidationResponse {
  valid: boolean;
  errors?: string[];
  sheet_names?: string[];
}

//Progreso de subida en tiempo real (para WebSocket)
export interface UploadProgress {
  percentage?: number;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  successful?: number;
  failed?: number;
  error?: string;
}
