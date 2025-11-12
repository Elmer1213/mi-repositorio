import { Component, OnInit, OnDestroy } from '@angular/core';
import { ExcelUploadService } from '../../services/excel-upload.service';
import {
  ExcelPreviewResponse,
  ExcelPreviewRow,
  UploadLog
} from '../../models/excel-upload.model';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-excel-upload',
  templateUrl: './excel-upload.component.html',
  styleUrls: ['./excel-upload.component.scss']
})
export class ExcelUploadComponent implements OnInit, OnDestroy {

  private destroy$ = new Subject<void>();

  // Archivo seleccionado
  selectedFile: File | null = null;
  isDragging = false;

  // Vista previa
  previewData: ExcelPreviewResponse | null = null;
  isLoadingPreview = false;

  // Progreso de subida
  uploadProgress = 0;
  isUploading = false;
  uploadComplete = false;

  // Registros del historial
  uploadLogs: UploadLog[] = [];
  isLoadingLogs = false;

  // Mensajes al usuario
  errorMessage = '';
  successMessage = '';

  constructor(private excelUploadService: ExcelUploadService) {}

  // -------------------- CICLO DE VIDA --------------------

  ngOnInit(): void {
    this.loadUploadLogs();
    this.subscribeToProgress();
    this.excelUploadService.connectWebSocket(); 
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.excelUploadService.disconnectWebSocket(); 
  }

  // -------------------- GETTERS PARA EL TEMPLATE --------------------

  /**
   * Obtiene las filas del preview (maneja rows y private_rows)
   */
  get previewRows(): ExcelPreviewRow[] {
    if (!this.previewData) return [];
    return this.previewData.rows || this.previewData.private_rows || [];
  }

  /**
   * Cantidad de filas inválidas en el preview
   */
  get invalidRowsCount(): number {
    return this.previewRows.filter(r => !r.is_valid).length;
  }

  /**
   * Verifica si hay errores en el preview
   */
  get hasPreviewErrors(): boolean {
    return this.previewData?.has_errors ?? false;
  }

  /**
   * Total de filas en el preview
   */
  get totalPreviewRows(): number {
    return this.previewData?.total_rows ?? 0;
  }

  /**
   * Verifica si se puede subir el archivo
   */
  get canUpload(): boolean {
    return !!(this.previewData && !this.hasPreviewErrors && !this.isUploading);
  }

  /**
   * Verifica si se puede previsualizar
   */
  get canPreview(): boolean {
    return !!(this.selectedFile && !this.isLoadingPreview);
  }

  // -------------------- SUBSCRIPCIONES --------------------

  private subscribeToProgress(): void {
    this.excelUploadService.progress$
      .pipe(takeUntil(this.destroy$))
      .subscribe(progress => {
        console.log('Progreso WS:', progress);

        if (progress.percentage !== undefined) {
          this.uploadProgress = progress.percentage;
        }

        if (progress.status === 'completed') {
          this.uploadComplete = true;
          this.successMessage = `Carga completada: ${progress.successful} filas exitosas, ${progress.failed} fallidas.`;

          setTimeout(() => {
            this.loadUploadLogs();
            this.resetUpload();
          }, 2000);
        }

        if (progress.status === 'failed') {
          this.errorMessage = progress.error || 'Error durante la carga';
          this.isUploading = false;
        }
      });

    this.excelUploadService.uploadProgress$
      .pipe(takeUntil(this.destroy$))
      .subscribe(p => this.uploadProgress = p);
  }

  // -------------------- DRAG & DROP --------------------

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
    const files = event.dataTransfer?.files;
    if (files?.length) this.handleFileSelection(files[0]);
  }

  // -------------------- SELECCIÓN DE ARCHIVO --------------------

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) this.handleFileSelection(input.files[0]);
  }

  private handleFileSelection(file: File): void {
    console.log('Archivo seleccionado:', file)
    this.clearMessages();
    this.previewData = null;

    // Validar tipo
    if (!/\.(xlsx|xls)$/i.test(file.name)) {
      this.errorMessage = 'Selecciona un archivo Excel (.xlsx o .xls)';
      return;
    }

    // Validar tamaño (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      this.errorMessage = 'El archivo supera el tamaño máximo de 10MB';
      console.log('Archivo muy grande:', file.size);
      return;
    }

    this.selectedFile = file;
    console.log('Archivo asignado a selectedFile:', this.selectedFile);
  }

  // -------------------- PREVISUALIZACIÓN --------------------

  loadPreview(): void {
    if (!this.selectedFile) return;

    this.isLoadingPreview = true;
    this.clearMessages();

    this.excelUploadService.previewExcel(this.selectedFile)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.previewData = response;
          this.isLoadingPreview = false;

          if (response.has_errors) {
            this.errorMessage = 'El archivo contiene errores. Revisa las filas marcadas en rojo.';
          } else {
            this.successMessage = `Preview generado: ${response.total_rows} filas detectadas.`;
          }
        },
        error: (error) => {
          this.isLoadingPreview = false;
          this.errorMessage = error.error?.detail || '❌ Error al generar el preview.';
          console.error('Error preview:', error);
        }
      });
  }

  // -------------------- SUBIDA --------------------

  uploadData(): void {
    if (!this.canUpload) {
      if (this.hasPreviewErrors) {
        this.errorMessage = '❌ No puedes subir un archivo con errores de validación.';
      }
      return;
    }

    this.isUploading = true;
    this.uploadComplete = false;
    this.clearMessages();

    this.excelUploadService.uploadExcel(this.selectedFile!)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.isUploading = false;
          this.uploadComplete = true;
          this.successMessage = `Carga iniciada: ${response.total_rows} filas serán procesadas.`;

          setTimeout(() => {
            this.loadUploadLogs();
            this.resetUpload();
          }, 2000);
        },
        error: (error) => {
          this.isUploading = false;
          this.errorMessage = error.error?.detail || '❌ Error al subir el archivo.';
          console.error('Error upload:', error);
        }
      });
  }

  // -------------------- LOGS --------------------

  loadUploadLogs(): void {
    this.isLoadingLogs = true;
    this.excelUploadService.getUploadLogs(50)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: logs => {
          this.uploadLogs = logs;
          this.isLoadingLogs = false;
        },
        error: error => {
          this.isLoadingLogs = false;
          console.error('Error cargando logs:', error);
        }
      });
  }

  // -------------------- UTILIDADES --------------------

  resetUpload(): void {
    this.selectedFile = null;
    this.previewData = null;
    this.uploadProgress = 0;
    this.uploadComplete = false;
    this.isUploading = false;
    this.excelUploadService.resetProgress();
  }

  clearMessages(): void {
    this.errorMessage = '';
    this.successMessage = '';
  }

  getStatusClass(status: string): string {
    const statusMap: Record<string, string> = {
      pending: 'status-pending',
      processing: 'status-processing',
      completed: 'status-completed',
      failed: 'status-failed'
    };
    return statusMap[status] || '';
  }

  getStatusText(status: string): string {
    const statusTextMap: Record<string, string> = {
      pending: 'Pendiente',
      processing: 'Procesando',
      completed: 'Completado',
      failed: 'Fallido'
    };
    return statusTextMap[status] || status;
  }

  // -------------------- DESCARGAR PLANTILLA --------------------

  downloadTemplate(): void {
    const csv = "name,email\nJuan Pérez,juan@example.com\nMaría García,maria@example.com";
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template_usuarios.csv';
    a.click();
    URL.revokeObjectURL(url);
  }
}