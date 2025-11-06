import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [{ path: 'sena', loadChildren: () => import('./modules/sena/sena.module').then(m => m.SenaModule) },
  { path: '', redirectTo: 'sena', pathMatch: 'full'}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
