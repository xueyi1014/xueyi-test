import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Home from '../views/Home.vue'

// 路由守卫：验证登录状态+身份权限
const requireAuth = (to, from, next) => {
  const token = localStorage.token
  const userRole = localStorage.userRole // 存储当前登录身份：student/teacher

  if (!token) {
    next('/') // 未登录跳登录页
  } else if (!userRole) {
    // 有token但无身份，强制选择身份
    localStorage.removeItem('token')
    next('/')
  } else {
    next()
  }
}

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    beforeEnter: requireAuth // 需要登录+身份验证
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router