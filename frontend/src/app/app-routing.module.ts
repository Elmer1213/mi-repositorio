import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'sena',
    pathMatch: 'full'
  },
  {
    path: 'sena',
    loadChildren: () =>
      import('./modules/sena/sena.module').then(m => m.SenaModule)
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: false })],
  exports: [RouterModule]
})
export class AppRoutingModule {}
