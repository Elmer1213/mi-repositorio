import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

// Interfaz del modelo de usuario (idéntica a la del backend)
export interface User {
  id?: number;
  name: string;
  email: string;
}

@Injectable({
  providedIn: 'root'
})
export class SenaService {
  private baseUrl = `${environment.apiUrl}/users`; 

  constructor(private http: HttpClient) {}

  // -----------------------------
  // GET - Obtener todos los usuarios
  // -----------------------------
  getAll(): Observable<User[]> {
    return this.http.get<User[]>(this.baseUrl);
  }

  // -----------------------------
  // POST - Crear usuario
  // -----------------------------
  create(user: User): Observable<User> {
    return this.http.post<User>(this.baseUrl, user);
  }

  // -----------------------------
  // PUT - Actualizar usuario
  // -----------------------------
  update(id: number, user: User): Observable<User> {
    return this.http.put<User>(`${this.baseUrl}/${id}`, user);
  }

  // -----------------------------
  // DELETE - Eliminar usuario
  // -----------------------------
  delete(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/${id}`);
  }
}
