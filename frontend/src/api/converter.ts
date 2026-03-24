import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ConversionFormat {
  type: string;
  from: string;
  to: string;
  description: string;
}

export interface ConversionResponse {
  task_id: string;
  status: string;
  filename: string;
  conversion_type: string;
}

export interface ConversionStatus {
  task_id: string;
  status: string;
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
  download_url?: string;
}

export const api = {
  async getFormats(): Promise<ConversionFormat[]> {
    const response = await axios.get(`${API_BASE_URL}/convert/formats`);
    return response.data.conversions;
  },

  async uploadAndConvert(file: File, conversionType: string): Promise<ConversionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversion_type', conversionType);

    const response = await axios.post(`${API_BASE_URL}/convert/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async getStatus(taskId: string): Promise<ConversionStatus> {
    const response = await axios.get(`${API_BASE_URL}/convert/status/${taskId}`);
    return response.data;
  },

  getDownloadUrl(taskId: string): string {
    return `${API_BASE_URL}/convert/download/${taskId}`;
  },

  async convertSync(file: File, conversionType: string, engine: string = 'auto'): Promise<Blob> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversion_type', conversionType);
    formData.append('engine', engine);

    const response = await axios.post(`${API_BASE_URL}/convert/sync`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });
    return response.data;
  },

  async healthCheck(): Promise<boolean> {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      return response.data.status === 'healthy';
    } catch {
      return false;
    }
  },
};
