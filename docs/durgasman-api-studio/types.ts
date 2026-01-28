
export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  PATCH = 'PATCH',
  DELETE = 'DELETE',
  HEAD = 'HEAD',
  OPTIONS = 'OPTIONS'
}

export type AppView = 'HOME' | 'BUILDER' | 'MOCKS' | 'SETTINGS' | 'DOCS';

export interface KeyValue {
  id: string;
  key: string;
  value: string;
  enabled: boolean;
}

export interface ApiRequest {
  id: string;
  name: string;
  method: HttpMethod;
  url: string;
  params: KeyValue[];
  headers: KeyValue[];
  body: string;
  authType: string;
  preRequestScript: string;
  testScript: string;
  responseSchema?: string;
}

export interface ApiResponse {
  status: number;
  statusText: string;
  time: number;
  size: string;
  headers: Record<string, string>;
  data: any;
  error?: string;
}

export interface Collection {
  id: string;
  name: string;
  requests: ApiRequest[];
  description?: string;
  aiDocs?: string;
}

export interface EnvVariable {
  id: string;
  key: string;
  value: string;
  enabled: boolean;
}

export interface Environment {
  id: string;
  name: string;
  variables: EnvVariable[];
}

export interface HistoryItem {
  id: string;
  timestamp: number;
  method: HttpMethod;
  url: string;
  body: string;
  headers: KeyValue[];
}

export interface MockEndpoint {
  id: string;
  path: string;
  method: HttpMethod;
  responseBody: string;
  responseSchema?: string;
  status: number;
  enabled: boolean;
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
  timestamp: number;
  groundingUrls?: string[];
}
