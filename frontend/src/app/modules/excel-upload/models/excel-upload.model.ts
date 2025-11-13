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
  sheet_name?: string
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
}

//Respuesta al subir Excel (backend -> frontend)
export interface UploadResponse {
  message: string;
  upload_id: number;
  total_rows: number;
}

//Respuesta de validación de archivo
export interface ValidationResponse {
  message: string;
  filename: string;
  size_ok: boolean;
  file_id: string;
  sheets: string[];
  total_sheets: number;
}

//Progreso de subida en tiempo real (para WebSocket)
export interface UploadProgress {
  current?: number;
  total?: number;
  percentage?: number;
  successful?: number;
  failed?: number;
  status?: 'processing' | 'completed' | 'failed' | 'connected';
  error?: string;
  type?: string;
  message?: string;
}

export interface SheetsResponse {
  sheets: string[];
  total: number;
  filename: string;
}

export interface ChartData {
  labels: string[];
  successful: number[];
  failed: number[];
  dates: string[];
}

export interface UploadStats {
  total_uploads: number;
  total_successful: number;
  total_failed: number;
  chart_data: ChartData;
}
