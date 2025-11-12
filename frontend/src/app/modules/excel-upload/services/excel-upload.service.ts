import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import {
  ExcelPreviewResponse,
  UploadLog,
  UploadResponse,
  ValidationResponse,
  UploadProgress
} from '../models/excel-upload.model';

@Injectable({
  providedIn: 'root'
})
export class ExcelUploadService {

  private apiUrl = 'http://localhost:8000/api/excel';
  private wsUrl = 'ws://localhost:8000/ws/upload-progress';
  private socket: WebSocket | null = null;

  // Progreso local (HTTP)
  private uploadProgressSubject = new BehaviorSubject<number>(0);
  public uploadProgress$ = this.uploadProgressSubject.asObservable();

  // Progreso WebSocket (mejor tipado con UploadProgress)
  private progressSubject = new BehaviorSubject<UploadProgress>({});
  public progress$ = this.progressSubject.asObservable();

  constructor(private http: HttpClient) {}

  // ======================================================
  // VALIDACIONES Y PREVISUALIZACIÓN
  // ======================================================

  validateFile(file: File): Observable<ValidationResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<ValidationResponse>(`${this.apiUrl}/validate-file`, formData);
  }

  getSheets(file: File): Observable<{ sheets: string[]; total: number }> {
    return this.http.get<{ sheets: string[]; total: number }>(`${this.apiUrl}/sheets`);
  }

  previewExcel(file: File): Observable<ExcelPreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<ExcelPreviewResponse>(`${this.apiUrl}/preview`, formData);
  }

  // ======================================================
  // SUBIDA DE ARCHIVO
  // ======================================================

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
        setTimeout(() => this.uploadProgressSubject.next(0), 2000);
      })
    );
  }

  // ======================================================
  //HISTORIAL DE CARGAS
  // ======================================================

  getUploadLogs(limit: number = 50): Observable<UploadLog[]> {
    return this.http.get<UploadLog[]>(`${this.apiUrl}/logs?limit=${limit}`);
  }

  getUploadLog(uploadId: number): Observable<UploadLog> {
    return this.http.get<UploadLog>(`${this.apiUrl}/logs/${uploadId}`);
  }

  // ======================================================
  // REINICIAR PROGRESO
  // ======================================================

  resetProgress(): void {
    this.uploadProgressSubject.next(0);
    this.progressSubject.next({});
  }

  // ======================================================
  // WEBSOCKET: CONEXIÓN Y MANEJO DE PROGRESO
  // ======================================================

  connectWebSocket(): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    this.socket = new WebSocket(this.wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket conectado');
    };

    this.socket.onmessage = (event) => {
      try {
        const data: UploadProgress = JSON.parse(event.data);
        console.log('Mensaje WS:', data);
        this.progressSubject.next(data);
      } catch (error) {
        console.error('Error al parsear mensaje WS:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onclose = () => {
      console.log('WebSocket desconectado');
    };
  }

  disconnectWebSocket(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      console.log('WebSocket cerrado manualmente');
    }
  }
}
