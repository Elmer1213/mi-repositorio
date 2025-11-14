import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

interface User {
  id?: number;
  name: string;
  email: string;
  createdAt?: Date;
}

@Component({
  selector: 'app-sena',
  templateUrl: './sena.component.html',
  styleUrls: ['./sena.component.scss']
})
export class SenaComponent implements OnInit {

  users: User[] = [];
  filteredUsers: User[] = [];
  paginatedUsers: User[] = [];
  newUser: User = { name: '', email: '' };
  editingUser: User | null = null;
  
  // Paginación
  currentPage: number = 1;
  pageSize: number = 10;
  
  // Búsqueda y filtros
  searchTerm: string = '';
  currentFilter: string = 'all';
  
  apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  ngOnInit() {
    this.getUsers();
  }

  // ==================== API CALLS ====================
  
  getUsers() {
    this.http.get<User[]>(`${this.apiUrl}/users/`).subscribe({
      next: (data) => {
        this.users = data;
        this.filterUsers();
      },
      error: (err) => {
        console.error('Error cargando usuarios:', err.message);
        console.log('Estado HTTP:', err.status);
        this.showNotification('Error al cargar usuarios', 'error');
      }
    });
  }

  saveUser() {
    if (!this.newUser.name || !this.newUser.email) {
      this.showNotification('Por favor completa todos los campos', 'warning');
      return;
    }

    if (!this.isValidEmail(this.newUser.email)) {
      this.showNotification('Por favor ingresa un correo válido', 'warning');
      return;
    }

    if (this.editingUser) {
      // Actualizar usuario existente
      this.http.put<User>(`${this.apiUrl}/users/${this.editingUser.id}`, this.newUser).subscribe({
        next: () => {
          this.showNotification('Usuario actualizado exitosamente', 'success');
          this.cancelEdit();
          this.getUsers();
        },
        error: (err) => {
          console.error('Error al actualizar usuario:', err.message);
          this.showNotification('Error al actualizar usuario', 'error');
        }
      });
    } else {
      // Crear nuevo usuario
      this.http.post<User>(`${this.apiUrl}/users/`, this.newUser).subscribe({
        next: (user) => {
          this.showNotification('Usuario agregado exitosamente', 'success');
          this.users.push(user);
          this.newUser = { name: '', email: '' };
          this.filterUsers();
        },
        error: (err) => {
          console.error('Error al crear usuario:', err.message);
          this.showNotification('Error al crear usuario', 'error');
        }
      });
    }
  }

  deleteUser(id?: number) {
    if (!id) return;
    
    if (confirm('¿Estás seguro de que deseas eliminar este usuario? Esta acción no se puede deshacer.')) {
      this.http.delete(`${this.apiUrl}/users/${id}`).subscribe({
        next: () => {
          this.showNotification('Usuario eliminado exitosamente', 'success');
          this.getUsers();
        },
        error: (err) => {
          console.error('Error al eliminar usuario:', err.message);
          this.showNotification('Error al eliminar usuario', 'error');
        }
      });
    }
  }

  // ==================== FORMULARIO ====================

  editUser(user: User) {
    this.editingUser = user;
    this.newUser = { ...user };
    this.scrollToForm();
  }

  cancelEdit() {
    this.editingUser = null;
    this.newUser = { name: '', email: '' };
  }

  resetForm(form: any) {
    form.resetForm();
    this.newUser = { name: '', email: '' };
    this.editingUser = null;
  }

  scrollToForm() {
    setTimeout(() => {
      const formCard = document.querySelector('.form-card');
      if (formCard) {
        formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  }

  // ==================== BÚSQUEDA Y FILTROS ====================

  filterUsers() {
    let filtered = [...this.users];

    // Aplicar búsqueda
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(user => 
        user.name.toLowerCase().includes(term) ||
        user.email.toLowerCase().includes(term) ||
        user.id?.toString().includes(term)
      );
    }

    // Aplicar filtros
    switch (this.currentFilter) {
      case 'recent':
        filtered.sort((a, b) => (b.id || 0) - (a.id || 0));
        break;
      case 'az':
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
      default:
        // 'all' - orden original
        break;
    }

    this.filteredUsers = filtered;
    this.currentPage = 1; // Reset a la primera página
    this.updatePaginatedUsers();
  }

  setFilter(filter: string) {
    this.currentFilter = filter;
    this.filterUsers();
  }

  // ==================== PAGINACIÓN ====================

  updatePaginatedUsers() {
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.paginatedUsers = this.filteredUsers.slice(startIndex, endIndex);
  }

  getTotalPages(): number {
    return Math.ceil(this.filteredUsers.length / this.pageSize);
  }

  getPageNumbers(): number[] {
    const totalPages = this.getTotalPages();
    const pages: number[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (this.currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i);
        pages.push(totalPages);
      } else if (this.currentPage >= totalPages - 2) {
        pages.push(1);
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push(this.currentPage - 1);
        pages.push(this.currentPage);
        pages.push(this.currentPage + 1);
        pages.push(totalPages);
      }
    }

    return pages;
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.getTotalPages()) {
      this.currentPage = page;
      this.updatePaginatedUsers();
    }
  }

  nextPage() {
    if (this.currentPage < this.getTotalPages()) {
      this.currentPage++;
      this.updatePaginatedUsers();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.updatePaginatedUsers();
    }
  }

  onPageSizeChange() {
    this.currentPage = 1;
    this.updatePaginatedUsers();
  }

  getStartIndex(): number {
    return (this.currentPage - 1) * this.pageSize;
  }

  getEndIndex(): number {
    const end = this.currentPage * this.pageSize;
    return end > this.filteredUsers.length ? this.filteredUsers.length : end;
  }

  // ==================== UTILIDADES ====================

  getInitials(name: string): string {
    if (!name) return '??';
    const words = name.trim().split(' ');
    if (words.length === 1) {
      return words[0].substring(0, 2).toUpperCase();
    }
    return (words[0][0] + words[words.length - 1][0]).toUpperCase();
  }

  isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  getNewUsersThisMonth(): number {
    // Esta es una función de ejemplo. 
    // En producción, deberías obtener esta información del backend
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();
    
    return this.users.filter(user => {
      if (!user.createdAt) return false;
      const createdDate = new Date(user.createdAt);
      return createdDate.getMonth() === currentMonth && 
             createdDate.getFullYear() === currentYear;
    }).length;
  }

  showNotification(message: string, type: 'success' | 'error' | 'warning' | 'info') {
    // Implementación simple con alert
    // En producción, deberías usar un servicio de notificaciones más sofisticado
    // como Angular Material Snackbar, NGX-Toastr, etc.
    
    const icons = {
      success: '✓',
      error: '✗',
      warning: '⚠',
      info: 'ℹ'
    };
    
    alert(`${icons[type]} ${message}`);
    
    // Alternativa: podrías crear un componente de notificación personalizado
    // o usar console con colores para desarrollo
    const styles = {
      success: 'color: #28a745; font-weight: bold;',
      error: 'color: #dc3545; font-weight: bold;',
      warning: 'color: #ffc107; font-weight: bold;',
      info: 'color: #17a2b8; font-weight: bold;'
    };
    
    console.log(`%c${message}`, styles[type]);
  }

  // ==================== MÉTODOS ADICIONALES ====================

  exportToCSV() {
    // Implementación para exportar a CSV
    const headers = ['ID', 'Nombre', 'Email'];
    const rows = this.filteredUsers.map(user => [
      user.id,
      user.name,
      user.email
    ]);
    
    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
      csvContent += row.join(',') + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `usuarios_sena_${new Date().getTime()}.csv`;
    link.click();
    
    this.showNotification('Archivo CSV exportado exitosamente', 'success');
  }

  printTable() {
    // Implementación simple para imprimir
    window.print();
  }

  // Método para refrescar la lista
  refreshUsers() {
    this.showNotification('Actualizando lista de usuarios...', 'info');
    this.getUsers();
  }

  // Método para seleccionar todos los usuarios (checkbox)
  selectAll(event: any) {
    // Implementación para checkbox de selección múltiple
    const checkboxes = document.querySelectorAll('.modern-table tbody .checkbox');
    checkboxes.forEach((checkbox: any) => {
      checkbox.checked = event.target.checked;
    });
  }

  // Método para acciones masivas
  bulkDelete() {
    const selectedCheckboxes = document.querySelectorAll('.modern-table tbody .checkbox:checked');
    if (selectedCheckboxes.length === 0) {
      this.showNotification('No hay usuarios seleccionados', 'warning');
      return;
    }
    
    if (confirm(`¿Deseas eliminar ${selectedCheckboxes.length} usuario(s)?`)) {
      // Implementar lógica de eliminación masiva
      this.showNotification('Funcionalidad en desarrollo', 'info');
    }
  }
}