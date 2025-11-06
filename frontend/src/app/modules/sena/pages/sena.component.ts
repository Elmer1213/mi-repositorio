import { Component, OnInit } from '@angular/core';
import { SenaService } from '../services/sena.service';

@Component({
  selector: 'app-sena',
  templateUrl: './sena.component.html',
  styleUrls: ['./sena.component.scss']
})
export class SenaComponent implements OnInit {

 newUser: { name: string; email: string } = { name: '', email: '' };

  // Aquí declaramos la variable que Angular necesita
  users: any[] = [];

  constructor(private senaService: SenaService) {}

  ngOnInit(): void {
    this.obtenerUsuarios();
  }

  obtenerUsuarios() {
    this.senaService.getAll().subscribe({
      next: (data: any) => {
        this.users = data;
        console.log('Usuarios obtenidos:', this.users);
      },
      error: (err: any) => {
        console.error('Error al obtener usuarios:', err);
      }
    });
  }

  createUser(): void {
    this.senaService.create(this.newUser).subscribe({
      next: (res: any) => {
        console.log('Usuario creado:', res);
        this.obtenerUsuarios();
        this.newUser = { name: '', email: '' }; 
      },
      error: (err: any) => {
        console.error('Error al crear usuario:', err);
      }
    });
  }
}
