import { TestBed } from '@angular/core/testing';

import { ServerServiceService } from './server.service.service';

describe('ServerServiceService', () => {
  let service: ServerServiceService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ServerServiceService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
