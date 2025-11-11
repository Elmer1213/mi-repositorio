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
      import('./modules/sena/modules/sena.module').then(m => m.SenaModule)
  },
  {
    path: 'excel-upload',
    loadChildren: () =>
      import('./modules/excel-upload/excel-upload.module').then(m => m.ExcelUploadModule)
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: false })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
