export interface Coordinates {
  x: number;
  y: number;
}

export interface Project {
  name: string;
  track: boolean;
  check_transparent_pixels: boolean;
  last_checked?: Date;
  griefed: boolean;
  api_image: string;
  start_coords: Coordinates;
  end_coords: Coordinates;
}

export interface ColorSetting {
  name: string;
  rgb: string;
  enabled: boolean;
}

export interface CheckResponse {
  message: string;
  response?: Project;
}

export interface AutomationSettings {
  automated_checks: boolean;
  discord_webhook: string;
  cooldown_between_checks: number;
}