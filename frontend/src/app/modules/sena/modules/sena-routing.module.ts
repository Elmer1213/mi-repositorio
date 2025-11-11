import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SenaComponent } from '../pages/sena.component';

const routes: Routes = [{ path: '', component: SenaComponent }];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class SenaRoutingModule { }
