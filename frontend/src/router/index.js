import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Home from '../views/Home.vue'
import ActivityList from '../views/ActivityList.vue'
import ActivityDetail from '../views/ActivityDetail.vue'
import CheckIn from '../views/CheckIn.vue'
import HourStats from '../views/HourStats.vue'
import UserCenter from '../views/UserCenter.vue'
import MyApplies from '../views/MyApplies.vue'
import MyFavorites from '../views/MyFavorites.vue'
import AppealPage from '../views/AppealPage.vue'
import TeacherHome from '../views/teacher/TeacherHome.vue'
import TeacherActivity from '../views/teacher/TeacherActivity.vue'
import TeacherApplies from '../views/teacher/TeacherApplies.vue'
import TeacherCheckin from '../views/teacher/TeacherCheckin.vue'
import TeacherViolation from '../views/teacher/TeacherViolation.vue'
import ExportHours from '../views/teacher/ExportHours.vue'
import GeneratePoster from '../views/teacher/GeneratePoster.vue'

// 路由守卫：验证登录状态+身份权限
const requireAuth = (to, from, next) => {
  const token = localStorage.token
  const userRole = localStorage.userRole

  if (!token) {
    next('/')
  } else if (!userRole) {
    localStorage.removeItem('token')
    next('/')
  } else {
    next()
  }
}

// 学生权限验证
const requireStudent = (to, from, next) => {
  const userRole = localStorage.userRole
  if (userRole === 'student') {
    next()
  } else {
    next('/home')
  }
}

// 老师权限验证
const requireTeacher = (to, from, next) => {
  const userRole = localStorage.userRole
  if (userRole === 'teacher') {
    next()
  } else {
    next('/home')
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
    beforeEnter: requireAuth
  },
  {
    path: '/activities',
    name: 'ActivityList',
    component: ActivityList,
    beforeEnter: requireAuth
  },
  {
    path: '/activity/:id',
    name: 'ActivityDetail',
    component: ActivityDetail,
    beforeEnter: requireAuth
  },
  {
    path: '/my-applies',
    name: 'MyApplies',
    component: MyApplies,
    beforeEnter: [requireAuth, requireStudent]
  },
  {
    path: '/my-favorites',
    name: 'MyFavorites',
    component: MyFavorites,
    beforeEnter: [requireAuth, requireStudent]
  },
  {
    path: '/checkin',
    name: 'CheckIn',
    component: CheckIn,
    beforeEnter: [requireAuth, requireStudent]
  },
  {
    path: '/hour-stats',
    name: 'HourStats',
    component: HourStats,
    beforeEnter: [requireAuth, requireStudent]
  },
  {
    path: '/appeal',
    name: 'AppealPage',
    component: AppealPage,
    beforeEnter: [requireAuth, requireStudent]
  },
  {
    path: '/teacher',
    name: 'TeacherHome',
    component: TeacherHome,
    beforeEnter: [requireAuth, requireTeacher]
  },
  {
    path: '/teacher/activity',
    name: 'TeacherActivity',
    component: TeacherActivity,
    beforeEnter: [requireAuth, requireTeacher]
  },
  {
    path: '/teacher/applies',
    name: 'TeacherApplies',
    component: TeacherApplies,
    beforeEnter: [requireAuth, requireTeacher]
  },
  {
    path: '/teacher/checkin',
    name: 'TeacherCheckin',
    component: TeacherCheckin,
    beforeEnter: [requireAuth, requireTeacher]
  },
  {
    path: '/teacher/violation',
    name: 'TeacherViolation',
    component: TeacherViolation,
    beforeEnter: [requireAuth, requireTeacher]
  },
  {
    path: '/teacher/export',
    name: 'ExportHours',
    component: ExportHours,
    beforeEnter: [requireAuth, requireTeacher]
  },
  {
    path: '/teacher/poster',
    name: 'GeneratePoster',
    component: GeneratePoster,
    beforeEnter: [requireAuth, requireTeacher]
  },
  {
    path: '/profile',
    name: 'UserCenter',
    component: UserCenter,
    beforeEnter: requireAuth
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router