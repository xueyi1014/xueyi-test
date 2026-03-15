// src/main.js 补充axios全局配置
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router/index.js'
// 新增：引入并配置axios
import axios from 'axios'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)

// 全局配置axios
app.config.globalProperties.$axios = axios
// 配置请求拦截器，自动携带token
axios.interceptors.request.use(config => {
  if (localStorage.token) {
    config.headers.Authorization = `Bearer ${localStorage.token}`
  }
  // 配置后端接口基础路径（根据你的后端地址修改）
  config.baseURL = 'http://localhost:8000' // 假设后端跑在8000端口
  return config
})

app.mount('#app')