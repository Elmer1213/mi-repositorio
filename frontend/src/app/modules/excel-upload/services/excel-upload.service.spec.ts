import { TestBed } from '@angular/core/testing';

import { ExcelUploadService } from './excel-upload.service';

describe('ExcelUploadService', () => {
  let service: ExcelUploadService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ExcelUploadService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
