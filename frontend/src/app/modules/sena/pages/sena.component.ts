import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

interface User {
  id?: number;
  name: string;
  email: string;
}

@Component({
  selector: 'app-sena',
  templateUrl: './sena.component.html',
  styleUrls: ['./sena.component.scss']
})
export class SenaComponent implements OnInit {

  users: User[] = [];
  newUser: User = { name: '', email: '' };
  // nuevo campo para saber si estamos editando
  editingUser: User | null = null;
  apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  ngOnInit() {
    this.getUsers();
  }

  // Obtener todos los usuarios
  getUsers() {
    this.http.get<User[]>(`${this.apiUrl}/users/`).subscribe({
      next: (data) => this.users = data,
      error: (err) => {
        console.error('Error cargando usuarios:', err.message);
        console.log('Estado HTTP:', err.status);
      }
    });
  }

  //Crear o actualizar usuario
  saveUser() {
    if (!this.newUser.name || !this.newUser.email) {
      alert('Por favor completa todos los campos.');
      return;
    }

    // Si estamos editando, usamos PUT
    if (this.editingUser) {
      this.http.put<User>(`${this.apiUrl}/users/${this.editingUser.id}`, this.newUser).subscribe({
        next: () => {
          this.cancelEdit();
          this.getUsers();
        },
        error: (err) => {
          console.error('Error al actualizar usuario:', err.message);
          console.log('Estado HTTP:', err.status);
        }
      });
    } else {
      // Si es nuevo, usamos POST
      this.http.post<User>(`${this.apiUrl}/users/`, this.newUser).subscribe({
        next: (user) => {
          this.users.push(user);
          // limpiar campos
          this.newUser = { name: '', email: '' };
        },
        error: (err) => {
          console.error('Error al crear usuario:', err.message);
          console.log('Estado HTTP:', err.status);
        }
      });
    }
  }

  //Seleccionar usuario para editar
  editUser(user: User) {
    this.editingUser = user;
    this.newUser = { ...user };
  }

  //Cancelar edición
  cancelEdit() {
    this.editingUser = null;
    this.newUser = { name: '', email: '' };
  }

  //Eliminar usuario
  deleteUser(id?: number) {
    if (!id) return;
    if (confirm('¿Seguro que deseas eliminar este usuario?')) {
      this.http.delete(`${this.apiUrl}/users/${id}`).subscribe({
        next: () => this.getUsers(),
        error: (err) => {
          console.error('Error al eliminar usuario:', err.message);
          console.log('Estado HTTP:', err.status);
        }
      });
    }
  }
}
