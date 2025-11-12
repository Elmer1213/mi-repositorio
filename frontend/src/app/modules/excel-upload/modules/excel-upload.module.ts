import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExcelUploadRoutingModule } from './excel-upload-routing.module';
import { ExcelUploadComponent } from '../components/excel-upload/excel-upload.component';

@NgModule({
  declarations: [ExcelUploadComponent],
  imports: [
    CommonModule,
    ExcelUploadRoutingModule
  ]
})
export class ExcelUploadModule { }
