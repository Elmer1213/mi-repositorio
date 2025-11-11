import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { 
  ExcelPreviewResponse, 
  UploadLog, 
  UploadResponse, 
  ValidationResponse 
} from '../models/excel-upload.model';

@Injectable({
  providedIn: 'root'
})
export class ExcelUploadService {
  
  private apiUrl = 'http://localhost:8000/api/excel';
  private wsUrl = 'ws://localhost:8000/ws/upload-progress';
  private socket: WebSocket | null = null;
  
  // Subject para el progreso de carga
  private uploadProgressSubject = new BehaviorSubject<number>(0);
  public uploadProgress$ = this.uploadProgressSubject.asObservable();

  constructor(private http: HttpClient) { }

  /**
   * Valida el archivo antes de subirlo
   */
  validateFile(file: File): Observable<ValidationResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.http.post<ValidationResponse>(`${this.apiUrl}/validate-file`, formData);
  }

  /**
   * Obtiene las hojas del archivo Excel
   */
  getSheets(file: File): Observable<{ sheets: string[], total: number }> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.http.get<{ sheets: string[], total: number }>(`${this.apiUrl}/sheets`);
  }

  /**
   * Obtiene un preview de los datos con validaciones
   */
  previewExcel(file: File): Observable<ExcelPreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.http.post<ExcelPreviewResponse>(`${this.apiUrl}/preview`, formData);
  }

  /**
   * Sube el archivo Excel a la base de datos
   */
  uploadExcel(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.http.post<UploadResponse>(`${this.apiUrl}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(
      map((event: HttpEvent<any>) => {
        if (event.type === HttpEventType.UploadProgress) {
          const progress = event.total 
            ? Math.round((100 * event.loaded) / event.total) 
            : 0;
          this.uploadProgressSubject.next(progress);
        } else if (event.type === HttpEventType.Response) {
          this.uploadProgressSubject.next(100);
          return event.body;
        }
        return null as any;
      }),
      tap(() => {
        // Reset progress after upload
        setTimeout(() => this.uploadProgressSubject.next(0), 2000);
      })
    );
  }

  /**
   * Obtiene el historial de cargas
   */
  getUploadLogs(limit: number = 50): Observable<UploadLog[]> {
    return this.http.get<UploadLog[]>(`${this.apiUrl}/logs?limit=${limit}`);
  }

  /**
   * Obtiene el detalle de una carga específica
   */
  getUploadLog(uploadId: number): Observable<UploadLog> {
    return this.http.get<UploadLog>(`${this.apiUrl}/logs/${uploadId}`);
  }

  /**
   * Resetea el progreso de carga
   */
  resetProgress(): void {
    this.uploadProgressSubject.next(0);
  }
}


  

  // ... resto del código existente ...

  /**
   * Conecta al WebSocket para recibir progreso en tiempo real
   */
  connectWebSocket(): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    this.socket = new WebSocket(this.wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket conectado');
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.progressSubject.next(data);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onclose = () => {
      console.log('WebSocket desconectado');
    };
  }

  /**
   * Desconecta el WebSocket
   */
  disconnectWebSocket(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
