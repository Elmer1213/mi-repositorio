import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ExcelUploadComponent } from '../components/excel-upload/excel-upload.component';

const routes: Routes = [
  { path: '', component: ExcelUploadComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ExcelUploadRoutingModule { }
