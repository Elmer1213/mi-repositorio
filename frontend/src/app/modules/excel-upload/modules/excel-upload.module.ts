import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { ExcelUploadRoutingModule } from './excel-upload-routing.module';
import { ExcelUploadComponent } from '../components/excel-upload/excel-upload.component';
import { StatsComponent } from '../../stats/stats.component';


const routes: Routes = [
  {
    path: '',
    component: ExcelUploadComponent
  },
  {
    path: 'stats',
    component: StatsComponent
  }
];

@NgModule({
  declarations: [ExcelUploadComponent],
  imports: [
    CommonModule,
    ExcelUploadRoutingModule
  ]
})
export class ExcelUploadModule { }
