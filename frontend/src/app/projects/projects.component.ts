import { Component, TemplateRef, inject, ViewChild, ElementRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgbModal, NgbModalConfig } from '@ng-bootstrap/ng-bootstrap';
import { NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { CommonModule } from '@angular/common';
import { ClipboardModule, Clipboard } from '@angular/cdk/clipboard';

import { ColorSetting, Project } from '../interfaces/arts.interface';

import { ToastServiceService } from '../services/toast.service.service';
import { ServerServiceService } from '../services/server.service.service';

import * as Prism from 'prismjs';
import 'prismjs/components/prism-javascript';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [FormsModule, NgbTooltipModule, CommonModule, ClipboardModule],
  providers: [NgbModalConfig, NgbModal],
  templateUrl: './projects.component.html',
  styleUrl: './projects.component.scss'
})
export class ProjectsComponent {
  constructor(
    public serverService: ServerServiceService,
    private modalService: NgbModal,
    private clipboard: Clipboard,
  ) { }

  @ViewChild('codeBlock') codeBlock?: ElementRef;

  artsData: Project[] = [];
  newProject: Project = {
    name: '',
    api_image: '',
    start_coords: { x: 0, y: 0 },
    end_coords: { x: 0, y: 0 },
    track: false,
    check_transparent_pixels: false,
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
  checkingAll: boolean = false;
  imageTimestamp: number = Date.now();
  reversedOrder: boolean = true;

  ngOnInit(): void {
    this.serverService.getAutomationSettings().subscribe((data) => {
      this.discordWebhook = data.discord_webhook;
      this.cooldownBetweenChecks = data.cooldown_between_checks;
      this.automatedChecks = data.automated_checks;
    });

    // Refresh projects list every 5 seconds
    this.listProjects();
    setInterval(() => {
      this.listProjects();
    }, 5000);
  }

  ngOnDestroy(): void {
		this.toastService.clear();
	}

  get displayedProjects(): Project[] {
    return this.reversedOrder ? [...this.artsData].reverse() : this.artsData;
  }

  listProjects(): void {
    this.serverService.listProjects().subscribe({
      next: (data) => {
        this.artsData = data;
      },
      error: (error: any) => {
        this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
      }
    });
  }

  toggleProjectOrder(): void {
    this.reversedOrder = !this.reversedOrder;
  }

  checkAllProjects(): void {
    this.toastService.show({ message: "Checking all projects..." });
    this.checkingAll = true;
    this.serverService.checkAllProjects().subscribe({
      next: (data) => {
        this.toastService.show({ message: data.message });
        this.checkingAll = false;

        if (!data.responses) {
          return;
        }

        data.responses.forEach((project: Project) => {
          const index = this.artsData.findIndex(p => p.name === project.name);
          console.log("Project checked:", project.name, project);
          if (index !== -1) {
            this.artsData[index] = project;
          }
        });

        // Update timestamp to force image reload
        this.imageTimestamp = Date.now();
      },
      error: (error: any) => {
        this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
        this.checkingAll = false;
      }
    });
  }

  checkProject(project: Project, event: MouseEvent): void {
    this.serverService.checkProject(project.name).subscribe({
      next: (data) => {
        this.toastService.show({ message: data.message });
        data.response!.name = project.name;
        const updatedProject = data.response!;
        const index = this.artsData.findIndex(p => p.name === project.name);
        if (index !== -1) {
          this.artsData[index] = updatedProject;
        }

        // Update timestamp to force image reload
        this.imageTimestamp = Date.now();
        
        if (this.selectedProject && this.selectedProject.name === updatedProject.name) {
          this.updateProject(updatedProject);
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

  updateProject(project: Project): void {
    this.serverService.getProjectLogs(project.name).subscribe({
      next: (data) => {
        this.terminalLogs = data.message;
      },
      error: (error: any) => {
        this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
        this.terminalLogs = null;
      }
    });

    this.serverService.getProjectFixCommand(project.name).subscribe({
      next: (data) => {
        this.fixCommand = data.message;
      }
    });

    if (project.griefed) {
      this.serverService.getProjectFixCommand(project.name).subscribe({
        next: (data) => {
          this.fixCommand = data.message;
          setTimeout(() => {
            this.conditionalHighlight();
          }, 50);
        },
        error: (error: any) => {
          this.toastService.show({ message: error.error.message, classname: 'bg-danger text-light', delay: 5000 });
        }
      });
    }
  }

  conditionalHighlight(): void {
    const maxLineLength = 2000; // Maximum characters per line
    
    document.querySelectorAll('pre code').forEach(block => {
      const text = (block as HTMLElement).textContent || '';
      const lines = text.split('\n');
      
      const hasLongLine = lines.some(line => line.length > maxLineLength);
      
      if (hasLongLine) {
        // Remove language class to prevent highlighting
        block.className = '';
        console.warn('Skipping Prism highlight: code contains lines exceeding', maxLineLength, 'characters');
      }
    });

    // Apply highlighting to remaining blocks
    Prism.highlightAll();
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

    // Update timestamp to force image reload when selecting project
    this.imageTimestamp = Date.now();
    this.updateProject(project);
  }

  onProjectChange(): void {
    if (this.selectedProject && this.editedProject) {
      console.log(JSON.stringify(this.selectedProject) !== JSON.stringify(this.editedProject), this.selectedProject, this.editedProject);
      this.hasChanges = JSON.stringify(this.selectedProject) !== JSON.stringify(this.editedProject);
    }
  }

  saveProjectChanges(): void {
    if (this.selectedProject && this.editedProject && this.hasChanges) {
      // Coordinates must be numbers
      this.editedProject.start_coords.x = Number(this.editedProject.start_coords.x);
      this.editedProject.start_coords.y = Number(this.editedProject.start_coords.y);
      this.editedProject.end_coords.x = Number(this.editedProject.end_coords.x);
      this.editedProject.end_coords.y = Number(this.editedProject.end_coords.y);

      // Name and api_image must be trimmed
      this.editedProject.name = this.editedProject.name.trim();
      this.editedProject.api_image = this.editedProject.api_image.trim();

      // Send update request
      this.serverService.updateProject(this.selectedProject.name, this.editedProject).subscribe({
        next: (data) => {
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

        if (!data.response) {
          return;
        }

        data.response.name = this.newProject.name;
        const index = this.artsData.findIndex(p => p.name === this.newProject.name);
        if (index !== -1) {
          this.artsData[index] = data.response;
        }
        this.selectProject(this.artsData[index]);
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
      this.clipboard.copy(this.fixCommand);
      this.copied = true;
      this.toastService.show({ message: 'Code copied to clipboard', classname: 'bg-success text-light' });
      setTimeout(() => this.copied = false, 1500);
    } else {
      this.toastService.show({ message: 'No code to copy', classname: 'bg-warning text-dark' });
    }
  }
}