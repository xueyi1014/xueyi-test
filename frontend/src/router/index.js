import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Home from '../views/Home.vue'

// 路由守卫：判断是否登录
const requireAuth = (to, from, next) => {
  if (localStorage.token) {
    next()
  } else {
    next('/')
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
    beforeEnter: requireAuth // 需要登录才能访问
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router