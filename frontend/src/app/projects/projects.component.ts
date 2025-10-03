import { Component, TemplateRef, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgbModal, NgbModalConfig } from '@ng-bootstrap/ng-bootstrap';
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { NgbOffcanvas } from '@ng-bootstrap/ng-bootstrap';
import { CommonModule, DATE_PIPE_DEFAULT_OPTIONS } from '@angular/common';

import { ColorSetting, Project } from '../interfaces/arts.interface';

import { ToastServiceService } from '../services/toast.service.service';
import { ServerServiceService } from '../services/server.service.service';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [FormsModule, NgbTooltipModule, CommonModule],
  providers: [NgbModalConfig, NgbModal],
  templateUrl: './projects.component.html',
  styleUrl: './projects.component.scss'
})
export class ProjectsComponent {
  constructor(public serverService: ServerServiceService, private modalService: NgbModal) { }
  artsData: Project[] = [];
  newProject: Project = {
    name: '',
    api_image: '',
    start_coords: { x: 0, y: 0 },
    end_coords: { x: 0, y: 0 },
    track: false,
    check_transparent_pixels: false,
    last_checked: new Date(),
    griefed: false
  };
  selectedProject: Project | null = null;
  automaticChecks: boolean = false;
  
	toastService = inject(ToastServiceService);
  errorMessage: string = '';

  colors: ColorSetting[] = [];

  offcanvasService = inject(NgbOffcanvas);

  discordWebhook: string = '';
  cooldownBetweenChecks: number = 300;
  automatedChecks: boolean = false;

  ngOnInit(): void {
    this.serverService.listProjects().subscribe((data) => {
      this.artsData = data;
    });
    this.serverService.getAutomationSettings().subscribe((data) => {
      this.discordWebhook = data.discord_webhook;
      this.cooldownBetweenChecks = data.cooldown_between_checks;
      this.automatedChecks = data.automated_checks;
    });
  }

  ngOnDestroy(): void {
		this.toastService.clear();
	}

  checkAllProjects(): void {
    this.serverService.checkAllProjects().subscribe((data) => {
      this.toastService.show({ message: data.message });
    });
  }

  checkProject(project: Project): void {
    this.serverService.checkProject(project.name).subscribe((data) => {
      this.toastService.show({ message: data.message });
    });
  }

  selectProject(project: Project): void {
    this.selectedProject = project;
  }

  checkAllProjectsAutomatically(): void {
    console.log("Automatic checks toggled:", this.automaticChecks);
  }

  saveProjectChanges(): void {
    if (this.selectedProject) {
      this.serverService.updateProject(this.selectedProject.name, this.selectedProject).subscribe((data) => {
        console.log("Project updated:", data);
      });
    }
  }

  deleteProject(project: Project): void {
    if (confirm(`Are you sure you want to delete the project "${project.name}"? This action cannot be undone.`)) {
      this.serverService.deleteProject(project.name).subscribe({
        next: (data) => {
          this.artsData = this.artsData.filter(p => p !== project);
          this.selectedProject = null;
          console.log("Project deleted:", data, data.message);
          this.toastService.show({ message: data.message, classname: 'bg-success text-light', delay: 5000 });
        },
        error: (error: any) => {
          this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
        }
      });
    }
  }

  openModal(content: TemplateRef<any>): void {
    this.modalService.open(content);
  }

  addNewProject(): void {
    this.serverService.addProject(this.newProject).subscribe({
      next: (data) => {
        this.artsData.push(this.newProject);
        this.modalService.dismissAll();
        this.toastService.show({ message: data.message, classname: 'bg-success text-light', delay: 5000 });
      },
      error: (error: any) => {
        console.error("Error adding project:", error.message);
        this.errorMessage = error.error.message;
      },
      complete: () => {
        this.newProject = {
          name: '',
          api_image: '',
          start_coords: { x: 0, y: 0 },
          end_coords: { x: 0, y: 0 },
          track: false,
          check_transparent_pixels: false,
          last_checked: new Date(),
          griefed: false
        };
        this.errorMessage = '';
      }
    });
  }

  loadColors(): void {
    this.serverService.getColors().subscribe({
      next: (data) => {
        this.colors = data;
      },
      error: (error: any) => {
        this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
      }
    });
  }

  saveColorSettings(): void {
    const colorSettings: { [key: string]: boolean } = {};
    this.colors.forEach(color => {
      colorSettings[color.name] = color.enabled;
    });
    this.serverService.updateColors(colorSettings).subscribe({
      next: (data) => {
        console.log("Color settings updated:", data);
        this.toastService.show({ message: data.message, classname: 'bg-success text-light', delay: 5000 });
      },
      error: (error: any) => {
        console.error("Error updating color settings:", error.message);
        this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
      }
    });
  }

  selectAllColors(): void {
    this.colors.forEach(color => color.enabled = true);
  }

  deselectAllColors(): void {
    this.colors.forEach(color => color.enabled = false);
  }

  openBottom(content: TemplateRef<any>) {
		this.offcanvasService.open(content, { position: 'bottom', backdrop: true });
	}

  updateAutomationSettings(): void {
    this.serverService.updateAutomationSettings(this.discordWebhook, this.cooldownBetweenChecks).subscribe({
      next: (data) => {
        this.toastService.show({ message: data.message, classname: 'bg-success text-light' });
      }
    });
  }

  toggleAutomationChecks(): void {
    this.serverService.toggleAutomatedChecks(!this.automatedChecks).subscribe({
      next: (data) => {
        this.automatedChecks = !this.automatedChecks;
        this.toastService.show({ message: data.message, classname: 'bg-success text-light' });
      }
    });
  }
}
