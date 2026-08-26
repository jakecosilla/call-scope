import type { BatchSummary, EvaluationMetrics, UploadResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiClient {
  private static token: string | null = localStorage.getItem('callscope_token');

  static setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('callscope_token', token);
    } else {
      localStorage.removeItem('callscope_token');
    }
  }

  static getToken(): string | null {
    return this.token;
  }

  static isAuthenticated(): boolean {
    return !!this.token;
  }

  private static getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = { ...extraHeaders };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  static async login(username: string, password: string): Promise<{ access_token: string; username: string }> {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: 'Authentication failed' }));
      throw new Error(errData.detail || 'Login failed');
    }

    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  static async uploadBatch(file: File, approach: 'approach_a' | 'approach_b'): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('approach', approach);

    const res = await fetch(`${API_BASE_URL}/api/batches`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: formData,
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: 'Batch upload failed' }));
      throw new Error(errData.detail || 'Upload failed');
    }

    return res.json();
  }

  static async getBatch(batchId: string): Promise<BatchSummary> {
    const res = await fetch(`${API_BASE_URL}/api/batches/${batchId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch batch status');
    }
    return res.json();
  }

  static async getEvaluation(batchId: string): Promise<EvaluationMetrics> {
    const res = await fetch(`${API_BASE_URL}/api/batches/${batchId}/evaluation`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch evaluation metrics');
    }
    return res.json();
  }

  static getExportCsvUrl(batchId: string): string {
    return `${API_BASE_URL}/api/batches/${batchId}/results.csv`;
  }

  static getExportJsonUrl(batchId: string): string {
    return `${API_BASE_URL}/api/batches/${batchId}/results.json`;
  }

  static async fetchExport(url: string, filename: string) {
    const res = await fetch(url, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Export download failed');
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(blobUrl);
  }
}
