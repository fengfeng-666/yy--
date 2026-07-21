import axios from 'axios'

import { apiBaseUrl } from '@/utils/env'

const http = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('yy-kitchen-access-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const message =
        typeof error.response?.data?.message === 'string'
          ? error.response.data.message
          : error.message
      return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  },
)

export default http
