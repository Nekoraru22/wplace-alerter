import { Component, inject } from '@angular/core';

import { NgbToastModule } from '@ng-bootstrap/ng-bootstrap';
import { ToastServiceService, Toast } from '../services/toast.service.service';

@Component({
	selector: 'app-toast',
	standalone: true,
	imports: [NgbToastModule],
	template: `
		@for (toast of toastService.toasts(); track toast) {
			<ngb-toast
				[class]="toast.classname"
				[autohide]="true"
				[delay]="toast.delay || 5000"
				(hidden)="toastService.remove(toast)"
			>
			<div class="d-flex">
				<div class="toast-header rounded">
					<strong class="me-auto">•ﻌ•</strong>
				</div>

				<div class="toast-body flex-grow-1">
					{{ toast.message }}
				</div>
			</div>
			</ngb-toast>
		}
	`,
	host: { class: 'toast-container position-fixed bottom-0 end-0 p-3', style: 'z-index: 1200' }
})
export class ToastComponent {
  readonly toastService = inject(ToastServiceService);
}
