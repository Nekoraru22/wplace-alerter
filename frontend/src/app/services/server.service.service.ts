import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Project, ColorSetting } from '../interfaces/arts.interface';

interface CheckResponse {
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ServerServiceService {
  private baseUrl = 'http://localhost:5000';

  constructor(private http: HttpClient) { }

  getBaseUrl(): string {
    return this.baseUrl + '/';
  }

  /**
   * Get all projects
   */
  listProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.baseUrl}/projects`);
  }

  /**
   * Check a specific project for changes
   * @param name - Project name
   */
  checkProject(name: string): Observable<CheckResponse> {
    return this.http.post<CheckResponse>(`${this.baseUrl}/projects/${name}/check`, null);
  }

  /**
   * Check all tracked projects for changes
   */
  checkAllProjects(): Observable<CheckResponse> {
    return this.http.post<CheckResponse>(`${this.baseUrl}/projects/check`, null);
  }

  /**
   * Update a project's properties
   * @param name - Project name
   * @param data - Partial project data to update
   */
  updateProject(name: string, data: Partial<Project>): Observable<CheckResponse> {
    return this.http.put<CheckResponse>(`${this.baseUrl}/projects/${name}/edit`, data);
  }

  /**
   * Add a new project
   * @param data - New project data
   */
  addProject(data: Project): Observable<CheckResponse> {
    return this.http.post<CheckResponse>(`${this.baseUrl}/projects`, data);
  }

  /**
   * Delete a project
   * @param name - Project name
   */
  deleteProject(name: string): Observable<CheckResponse> {
    return this.http.delete<CheckResponse>(`${this.baseUrl}/projects/${name}`);
  }

  /**
   * Get color settings
   */
  getColors(): Observable<ColorSetting[]> {
    return this.http.get<ColorSetting[]>(`${this.baseUrl}/config/colors`);
  }

  /**
   * Update color settings
   * @param colors - Array of color settings to update
   */
  updateColors(colors: { [key: string]: boolean }): Observable<CheckResponse> {
    return this.http.put<CheckResponse>(`${this.baseUrl}/config/colors`, { colors });
  } 
}