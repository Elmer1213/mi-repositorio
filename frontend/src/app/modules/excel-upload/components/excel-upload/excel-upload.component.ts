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
  
  // File management
  selectedFile: File | null = null;
  isDragging = false;
  
  // Preview data
  previewData: ExcelPreviewResponse | null = null;
  isLoadingPreview = false;
  
  // Upload progress
  uploadProgress = 0;
  isUploading = false;
  uploadComplete = false;
  
  // Logs
  uploadLogs: UploadLog[] = [];
  isLoadingLogs = false;
  
  // Messages
  errorMessage = '';
  successMessage = '';

  constructor(private excelUploadService: ExcelUploadService) {}

  ngOnInit(): void {
    this.loadUploadLogs();
    this.subscribeToProgress();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Suscribe al progreso de carga
   */
  private subscribeToProgress(): void {
    this.excelUploadService.uploadProgress$
      .pipe(takeUntil(this.destroy$))
      .subscribe(progress => {
        this.uploadProgress = progress;
      });
  }

  /**
   * Manejo de drag & drop
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFileSelection(files[0]);
    }
  }

  /**
   * Manejo de selección de archivo
   */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFileSelection(input.files[0]);
    }
  }

  /**
   * Procesa el archivo seleccionado
   */
  private handleFileSelection(file: File): void {
    this.clearMessages();
    this.previewData = null;
    
    // Validar extensión
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      this.errorMessage = 'Por favor selecciona un archivo Excel (.xlsx o .xls)';
      return;
    }

    // Validar tamaño (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      this.errorMessage = 'El archivo excede el tamaño máximo de 10MB';
      return;
    }

    this.selectedFile = file;
    this.loadPreview();
  }

  /**
   * Carga el preview de los datos
   */
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
            this.errorMessage = 'El archivo contiene errores de validación. Por favor revisa las filas marcadas en rojo.';
          } else {
            this.successMessage = `Preview cargado correctamente. ${response.total_rows} filas detectadas.`;
          }
        },
        error: (error) => {
          this.isLoadingPreview = false;
          this.errorMessage = error.error?.detail || 'Error al cargar el preview del archivo';
          console.error('Error loading preview:', error);
        }
      });
  }

  /**
   * Sube los datos a la base de datos
   */
  uploadData(): void {
    if (!this.selectedFile || !this.previewData) return;

    if (this.previewData.has_errors) {
      this.errorMessage = 'No se puede subir un archivo con errores de validación';
      return;
    }

    this.isUploading = true;
    this.uploadComplete = false;
    this.clearMessages();

    this.excelUploadService.uploadExcel(this.selectedFile)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response) {
            this.isUploading = false;
            this.uploadComplete = true;
            this.successMessage = `¡Carga exitosa! Se procesarán ${response.total_rows} filas.`;
            
            // Recargar logs después de 2 segundos
            setTimeout(() => {
              this.loadUploadLogs();
              this.resetUpload();
            }, 2000);
          }
        },
        error: (error) => {
          this.isUploading = false;
          this.errorMessage = error.error?.detail || 'Error al subir el archivo';
          console.error('Error uploading file:', error);
        }
      });
  }

  /**
   * Carga el historial de cargas
   */
  loadUploadLogs(): void {
    this.isLoadingLogs = true;
    
    this.excelUploadService.getUploadLogs(50)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (logs) => {
          this.uploadLogs = logs;
          this.isLoadingLogs = false;
        },
        error: (error) => {
          this.isLoadingLogs = false;
          console.error('Error loading logs:', error);
        }
      });
  }

  /**
   * Resetea el estado de carga
   */
  resetUpload(): void {
    this.selectedFile = null;
    this.previewData = null;
    this.uploadProgress = 0;
    this.uploadComplete = false;
    this.excelUploadService.resetProgress();
  }

  /**
   * Limpia los mensajes
   */
  clearMessages(): void {
    this.errorMessage = '';
    this.successMessage = '';
  }

  /**
   * Obtiene la clase CSS según el estado
   */
  getStatusClass(status: string): string {
    const statusClasses: { [key: string]: string } = {
      'pending': 'status-pending',
      'processing': 'status-processing',
      'completed': 'status-completed',
      'failed': 'status-failed'
    };
    return statusClasses[status] || '';
  }

  /**
   * Obtiene el texto del estado en español
   */
  getStatusText(status: string): string {
    const statusTexts: { [key: string]: string } = {
      'pending': 'Pendiente',
      'processing': 'Procesando',
      'completed': 'Completado',
      'failed': 'Fallido'
    };
    return statusTexts[status] || status;
  }

  /**
   * Descarga un template de Excel
   */
  downloadTemplate(): void {
    // Aquí podrías generar un template o descargar uno predefinido
    const csvContent = "name,email\nJuan Pérez,juan@example.com\nMaría García,maria@example.com";
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'template_usuarios.csv';
    link.click();
    window.URL.revokeObjectURL(url);
  }
}

ngOnInit(): void {
  this.loadUploadLogs();
  this.subscribeToProgress();
  this.excelUploadService.connectWebSocket(); // Conectar WebSocket
}

ngOnDestroy(): void {
  this.destroy$.next();
  this.destroy$.complete();
  this.excelUploadService.disconnectWebSocket(); // Desconectar
}

/**
 * Suscribe al progreso de WebSocket
 */
private subscribeToProgress(): void {
  this.excelUploadService.progress$
    .pipe(takeUntil(this.destroy$))
    .subscribe(progress => {
      console.log('Progreso:', progress);
      
      if (progress.percentage) {
        this.uploadProgress = progress.percentage;
      }
      
      if (progress.status === 'completed') {
        this.uploadComplete = true;
        this.successMessage = `¡Carga completada! ${progress.successful} exitosos, ${progress.failed} fallidos`;
        setTimeout(() => {
          this.loadUploadLogs();
          this.resetUpload();
        }, 2000);
      }
      
      if (progress.status === 'failed') {
        this.errorMessage = progress.error || 'Error en la carga';
        this.isUploading = false;
      }
    });
}