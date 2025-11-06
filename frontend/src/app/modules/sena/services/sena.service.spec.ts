import { TestBed } from '@angular/core/testing';

import { SenaService } from './sena.service';

describe('SenaService', () => {
  let service: SenaService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SenaService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
