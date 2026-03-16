import axios from 'axios'

const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',  // 后端地址（必须和后端运行地址一致）
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加token
request.interceptors.request.use(
  config => {
    if (localStorage.token) {
      config.headers.Authorization = `Bearer ${localStorage.token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

export default request