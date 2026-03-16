import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router/index.js'
import axios from 'axios'

const app = createApp(App)

// 全局配置 axios
app.config.globalProperties.$axios = axios

// 请求拦截器：每次发请求自动带 token
axios.interceptors.request.use(config => {
  if (localStorage.token) {
    config.headers.Authorization = `Bearer ${localStorage.token}`
  }
  config.baseURL = 'http://127.0.0.1:8000'
  return config
})

app.use(ElementPlus)
app.use(router)
app.mount('#app')