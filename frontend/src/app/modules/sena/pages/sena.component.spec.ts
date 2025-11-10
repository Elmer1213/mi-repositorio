import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SenaComponent } from './sena.component';

describe('SenaComponent', () => {
  let component: SenaComponent;
  let fixture: ComponentFixture<SenaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SenaComponent]
    })
      .compileComponents();

    fixture = TestBed.createComponent(SenaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
