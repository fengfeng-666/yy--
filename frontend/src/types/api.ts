export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface HealthCheckData {
  app_name: string
  environment: string
  status: 'ok'
}
