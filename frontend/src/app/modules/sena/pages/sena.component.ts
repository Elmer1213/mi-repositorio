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
  apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.getUsers();
  }

  getUsers() {
    this.http.get<User[]>(`${this.apiUrl}/users/`).subscribe({
      next: (data) => this.users = data,
      error: (err) => console.error('Error cargando usuarios:', err)
    });
  }

  addUser() {
    if (!this.newUser.name || !this.newUser.email) return;

    this.http.post<User>(`${this.apiUrl}/users/`, this.newUser).subscribe({
      next: (user) => {
        this.users.push(user);
         // limpiar campos
        this.newUser = { name: '', email: '' };
      },
      error: (err) => console.error('Error al crear usuario:', err)
    });
  }
}
