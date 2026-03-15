import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Home from '../views/Home.vue'
import ActivityList from '../views/ActivityList.vue'
import ActivityDetail from '../views/ActivityDetail.vue'
import UserCenter from '../views/UserCenter.vue'

const routes = [
  { path: '/', component: Login },
  { path: '/register', component: Register },
  { path: '/home', component: Home },
  { path: '/activity', component: ActivityList },
  { path: '/activity/:id', component: ActivityDetail },
  { path: '/user', component: UserCenter },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router