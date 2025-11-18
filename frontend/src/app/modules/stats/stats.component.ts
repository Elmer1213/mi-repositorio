import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { ExcelUploadService } from '../excel-upload/services/excel-upload.service';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-stats',
  templateUrl: './stats.component.html',
  styleUrls: ['./stats.component.scss']
})
export class StatsComponent implements OnInit, AfterViewInit {
  @ViewChild('barChartCanvas') barChartCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('lineChartCanvas') lineChartCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('pieChartCanvas') pieChartCanvas!: ElementRef<HTMLCanvasElement>;

  barChart?: Chart;
  lineChart?: Chart;
  pieChart?: Chart;

  stats: any = null;
  isLoading: boolean = false;
  chartsReady: boolean = false;

  colors = {
    primary: '#3498db',
    success: '#27ae60',
    danger: '#e74c3c',
    warning: '#f39c12',
    info: '#16a085'
  };

  constructor(private excelUploadService: ExcelUploadService) { }

  ngOnInit(): void {
    this.loadStats();
  }

  ngAfterViewInit(): void {
    this.chartsReady = true;
    if (this.stats && this.stats.chart_data) {
      setTimeout(() => this.createCharts(), 100);
    }
  }

  loadStats(): void {
    this.isLoading = true;

    this.excelUploadService.getUploadStats().subscribe({
      next: (data) => {
        console.log('Estadísticas cargadas:', data);
        console.log('chart_data:', data.chart_data);

        this.stats = data;
        this.isLoading = false;

        // Esperar a que los ViewChild estén disponibles
        if (this.chartsReady) {
          setTimeout(() => this.createCharts(), 100);
        }
      },
      error: (error) => {
        console.error('Error al cargar estadísticas:', error);
        this.isLoading = false;
      }
    });
  }

  createCharts(): void {
    if (!this.stats || !this.stats.chart_data) {
      console.warn('No hay datos para crear gráficos');
      console.log('stats:', this.stats);
      return;
    }

    console.log('Creando gráficos...');

    try {
      this.createBarChart();
      this.createLineChart();
      this.createPieChart();
      console.log('Gráficos creados exitosamente');
    } catch (error) {
      console.error('Error al crear gráficos:', error);
    }
  }

  createBarChart(): void {
    if (!this.barChartCanvas) {
      console.warn('barChartCanvas no disponible');
      return;
    }

    const ctx = this.barChartCanvas.nativeElement.getContext('2d');
    if (!ctx) {
      console.error('No se pudo obtener el contexto del canvas');
      return;
    }

    if (this.barChart) {
      this.barChart.destroy();
    }

    const chartData = this.stats.chart_data;

    // Validar que existan los datos necesarios
    if (!chartData.labels || !chartData.successful || !chartData.failed) {
      console.error('Faltan datos para el gráfico de barras:', chartData);
      return;
    }

    console.log('Creando gráfico de barras con:', {
      labels: chartData.labels,
      successful: chartData.successful,
      failed: chartData.failed
    });

    const config: ChartConfiguration = {
      type: 'bar',
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: 'Filas Exitosas',
            data: chartData.successful,
            backgroundColor: this.colors.success,
            borderColor: this.colors.success,
            borderWidth: 1
          },
          {
            label: 'Filas Fallidas',
            data: chartData.failed,
            backgroundColor: this.colors.danger,
            borderColor: this.colors.danger,
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Resultados de Carga por Archivo',
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            position: 'bottom'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Número de Filas'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Archivos Cargados'
            }
          }
        }
      }
    };

    this.barChart = new Chart(ctx, config);
  }

  createLineChart(): void {
    if (!this.lineChartCanvas) {
      console.warn('lineChartCanvas no disponible');
      return;
    }

    const ctx = this.lineChartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    if (this.lineChart) {
      this.lineChart.destroy();
    }

    const chartData = this.stats.chart_data;

    // Usar dates si existe, sino usar labels
    const labels = chartData.dates || chartData.labels;

    if (!labels || !chartData.successful || !chartData.failed) {
      console.error('Faltan datos para el gráfico de líneas');
      return;
    }

    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Filas Exitosas',
            data: chartData.successful,
            borderColor: this.colors.success,
            backgroundColor: this.colors.success + '20',
            fill: true,
            tension: 0.4
          },
          {
            label: 'Filas Fallidas',
            data: chartData.failed,
            borderColor: this.colors.danger,
            backgroundColor: this.colors.danger + '20',
            fill: true,
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Tendencia de Cargas en el Tiempo',
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            position: 'bottom'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Número de Filas'
            }
          }
        }
      }
    };

    this.lineChart = new Chart(ctx, config);
  }

  createPieChart(): void {
    if (!this.pieChartCanvas) {
      console.warn('pieChartCanvas no disponible');
      return;
    }

    const ctx = this.pieChartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    if (this.pieChart) {
      this.pieChart.destroy();
    }

    const config: ChartConfiguration = {
      type: 'doughnut',
      data: {
        labels: ['Exitosas', 'Fallidas'],
        datasets: [{
          data: [this.stats.total_successful, this.stats.total_failed],
          backgroundColor: [this.colors.success, this.colors.danger],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Proporción Total',
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            position: 'bottom'
          }
        }
      }
    };

    this.pieChart = new Chart(ctx, config);
  }

  refresh(): void {
    if (this.barChart) this.barChart.destroy();
    if (this.lineChart) this.lineChart.destroy();
    if (this.pieChart) this.pieChart.destroy();

    this.loadStats();
  }

  getSuccessRate(): number {
    if (!this.stats) return 0;
    const total = this.stats.total_successful + this.stats.total_failed;
    if (total === 0) return 0;
    return (this.stats.total_successful / total) * 100;
  }

  formatNumber(num: number): string {
    return num.toLocaleString('es-CO');
  }
}