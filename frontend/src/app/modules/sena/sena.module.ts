import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SenaRoutingModule } from './sena-routing.module';
import { SenaComponent } from './pages/sena.component';
import { FormsModule } from '@angular/forms';


@NgModule({
  declarations: [SenaComponent],
  imports: [
    CommonModule,
    SenaRoutingModule,
    FormsModule
  ],
  exports: [SenaComponent]
})
export class SenaModule { }
