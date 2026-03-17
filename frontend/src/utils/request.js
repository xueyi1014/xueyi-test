import axios from 'axios'

// 创建axios实例，适配后端地址
const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',  // 后端固定地址（必须和后端启动地址一致）
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  }
})

// 请求拦截器：添加token
request.interceptors.request.use(
  (config) => {
    if (localStorage.getItem('token')) {
      config.headers.Authorization = `Bearer ${localStorage.getItem('token')}`
    }
    return config
  },
  (error) => {
    console.error('请求拦截错误：', error)
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理返回值
request.interceptors.response.use(
  (response) => {
    // 直接返回响应数据
    return response.data
  },
  (error) => {
    console.error('响应错误：', error)
    // 统一错误提示
    const msg = error.response?.data?.msg || error.message || '请求失败'
    // 这里可以引入Element Plus的Message提示
    if (window.ElMessage) {
      window.ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request