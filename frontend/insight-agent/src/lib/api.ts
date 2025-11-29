/**
 * API client for backend communication
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Ticker {
  tickers: string[];
  default: string;
}

export interface Recommendation {
  index: number;
  date: string | null;
  rating: string | null;
  analyst: string;
  ticker: string;
  company: string;
  cusip: string;
}

export interface ExplainerRequest {
  rec_index: number;
  fund_window_days: number;
  news_window_days: number;
}

export interface RecommenderRequest {
  rec_index: number;
  news_window_days: number;
  ticker: string;
  company: string;
}

export interface JobResponse {
  status: 'processing' | 'completed' | 'error';
  job_id: string;
  message: string;
}

export interface JobStatus {
  status: 'processing' | 'completed' | 'error';
  result: {
    manager_report: string;
    analyst_reports: {
      fundamental: string;
      technical: string;
      news: string;
    };
    full_markdown: string;
    final_rating?: string;
    human_rating?: string;
  } | null;
  error: string | null;
}

export interface Config {
  defaults: {
    explainer: {
      fund_window_days: number;
      news_window_days: number;
      technical_window_days: number;
    };
    recommender: {
      news_window_days: number;
    };
  };
};

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    console.log(`API Request: ${options.method || 'GET'} ${url}`);
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      console.log(`API Response: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const error = await response.text();
        console.error(`API Error: ${response.status} - ${error}`);
        throw new Error(`API Error: ${response.status} - ${error}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('Network error - is backend running?', error);
        throw new Error(`Cannot connect to backend at ${this.baseURL}. Make sure the backend is running on port 8000.`);
      }
      throw error;
    }
  }

  async getTickers(): Promise<Ticker> {
    return this.request<Ticker>('/api/tickers');
  }

  async getRecommendations(
    ticker: string,
    mode: 'explainer' | 'recommender'
  ): Promise<{ recommendations: Recommendation[] }> {
    return this.request<{ recommendations: Recommendation[] }>(
      `/api/recommendations?ticker=${ticker}&mode=${mode}`
    );
  }

  async runExplainer(request: ExplainerRequest): Promise<JobResponse> {
    return this.request<JobResponse>('/api/explainer/run', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getExplainerStatus(jobId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/api/explainer/status/${jobId}`);
  }

  async runRecommender(request: RecommenderRequest): Promise<JobResponse> {
    return this.request<JobResponse>('/api/recommender/run', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getRecommenderStatus(jobId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/api/recommender/status/${jobId}`);
  }

  async getConfig(): Promise<Config> {
    return this.request<Config>('/api/config');
  }

  async pollJobStatus(
    jobId: string,
    mode: 'explainer' | 'recommender',
    onProgress?: (status: JobStatus) => void
  ): Promise<JobStatus> {
    const poll = async (): Promise<JobStatus> => {
      const status =
        mode === 'explainer'
          ? await this.getExplainerStatus(jobId)
          : await this.getRecommenderStatus(jobId);

      if (onProgress) {
        onProgress(status);
      }

      if (status.status === 'completed') {
        return status;
      } else if (status.status === 'error') {
        throw new Error(status.error || 'Job failed');
      } else {
        // Still processing, poll again in 2.5 seconds
        await new Promise((resolve) => setTimeout(resolve, 2500));
        return poll();
      }
    };

    return poll();
  }
}

export const apiClient = new ApiClient();

