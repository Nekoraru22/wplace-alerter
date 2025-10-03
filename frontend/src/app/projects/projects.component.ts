import { Component, TemplateRef, inject, ViewChild, ElementRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgbModal, NgbModalConfig } from '@ng-bootstrap/ng-bootstrap';
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { CommonModule } from '@angular/common';

import { ColorSetting, Project } from '../interfaces/arts.interface';

import { ToastServiceService } from '../services/toast.service.service';
import { ServerServiceService } from '../services/server.service.service';

import * as Prism from 'prismjs';
import 'prismjs/components/prism-javascript';

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

  @ViewChild('codeBlock') codeBlock?: ElementRef;

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
  editedProject: Project | null = null;
  terminalLogs: string | null = null;
  fixCommand: string | null = null;
  copied: boolean = false;
  hasChanges: boolean = false;
  automaticChecks: boolean = false;
  
	toastService = inject(ToastServiceService);
  errorMessage: string = '';

  colors: ColorSetting[] = [];

  discordWebhook: string = '';
  cooldownBetweenChecks: number = 300;
  automatedChecks: boolean = false;

  isImgLoading: boolean = true;

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

  highlightCode() {
    setTimeout(() => {
      if (this.codeBlock?.nativeElement) {
        Prism.highlightElement(this.codeBlock.nativeElement);
      }
    }, 100);
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
    this.serverService.checkProject(project.name).subscribe({
      next: (data) => {
        this.toastService.show({ message: data.message });
        this.selectedProject = data.response!;
        const index = this.artsData.findIndex(p => p.name === project.name);
        if (index !== -1) {
          this.artsData[index] = this.selectedProject;
        }
      },
      error: (error: any) => {
        this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
      }
    });
  }

  checkAllProjectsAutomatically(): void {
    this.toastService.show({ message: "Automatic checks toggled:" });
  }

  selectProject(project: Project): void {
    this.selectedProject = project;
    this.editedProject = JSON.parse(JSON.stringify(project));
    this.hasChanges = false;

    if (project.name != this.selectedProject?.name) {
      this.isImgLoading = true;
      this.terminalLogs = null;
      this.fixCommand = null;
    }

    this.serverService.getProjectLogs(project.name).subscribe({
      next: (data) => {
        this.terminalLogs = data.message;
      },
      error: (error: any) => {
        this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
        this.terminalLogs = null;
      }
    });

    if (project.griefed) {
      this.serverService.getProjectFixCommand(project.name).subscribe({
        next: (data) => {
          this.fixCommand = data.message;
          setTimeout(() => {
            Prism.highlightAll();
          }, 50);
        },
        error: (error: any) => {
          this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
        }
      });
    }
  }

  onProjectChange(): void {
    if (this.selectedProject && this.editedProject) {
      this.hasChanges = JSON.stringify(this.selectedProject) !== JSON.stringify(this.editedProject);
    }
  }

  saveProjectChanges(): void {
    if (this.selectedProject && this.editedProject && this.hasChanges) {
      this.serverService.updateProject(this.selectedProject.name, this.editedProject).subscribe({
        next: (data) => {
          console.log("Project updated:", data);
          Object.assign(this.selectedProject!, this.editedProject!);
          const index = this.artsData.findIndex(p => p.name === this.selectedProject!.name);
          if (index !== -1) {
            this.artsData[index] = this.selectedProject!;
          }
          this.hasChanges = false;
          this.toastService.show({ message: data.message, classname: 'bg-success text-light', delay: 5000 });
        },
        error: (error: any) => {
          this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
        }
      });
    }
  }

  deleteProject(project: Project): void {
    if (confirm(`Are you sure you want to delete the project "${project.name}"? This action cannot be undone.`)) {
      this.serverService.deleteProject(project.name).subscribe({
        next: (data) => {
          this.artsData = this.artsData.filter(p => p !== project);
          this.selectedProject = null;
          this.editedProject = null;
          this.hasChanges = false;
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
    this.modalService.open(content, { centered: true });
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

  selectFree(): void {
    this.colors.forEach(color => {
      if ([
        'TRANSPARENT', 'BLACK', 'DARK_GRAY', 'GRAY', 'LIGHT_GRAY', 'WHITE', 'DEEP_RED', 'RED', 'ORANGE', 'GOLD',
        'YELLOW', 'LIGHT_YELLOW', 'DARK_GREEN', 'GREEN', 'LIGHT_GREEN', 'DARK_TEAL', 'TEAL', 'LIGHT_TEAL', 'DARK_BLUE',
        'BLUE', 'CYAN', 'INDIGO', 'LIGHT_INDIGO', 'DARK_PURPLE', 'PURPLE', 'LIGHT_PURPLE', 'DARK_PINK', 'PINK',
        'LIGHT_PINK', 'DARK_BROWN', 'BROWN', 'BEIGE'
      ].includes(color.name)) {
        color.enabled = true;
      } else {
        color.enabled = false;
      }
    });
  }

  openBottom(content: TemplateRef<any>) {
    this.modalService.open(content, { centered: true, scrollable: true, windowClass: 'modal-bottom' });
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

  getStatus(project: Project): string {
    if (project.track === false) {
      return 'status-circle-gray';
    } else {
      return project.griefed ? 'status-circle-red' : 'status-circle-green';
    }
  }

  onImageError(event: Event) {
    const element = event.target as HTMLImageElement;
    element.src = 'assets/logo.gif';
  }

  copyCode(): void {
    if (this.fixCommand) {
      navigator.clipboard.writeText(this.fixCommand).then(() => {
        this.copied = true;
        setTimeout(() => {
          this.copied = false;
        }, 2000);
      }).catch(err => {
        console.error('Error copying code:', err);
        this.toastService.show({ 
          message: 'Failed to copy code', 
          classname: 'bg-danger text-light', 
          delay: 3000 
        });
      });
    }
  }
}
