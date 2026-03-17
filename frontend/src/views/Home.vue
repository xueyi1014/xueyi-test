<template>
  <div class="admin-layout">
    <!-- 顶部导航 -->
    <el-header class="header">
      <div class="header-left">
        <h2>校园志愿服务管理系统</h2>
      </div>
      <div class="header-right">
        <el-tag size="small" type="primary">角色：{{ userRole === 'student' ? '学生' : '老师' }}</el-tag>
        <span class="user-info">
          <el-avatar icon="el-icon-user" size="small"></el-avatar>
          {{ username }}
        </span>
        <el-button size="small" link type="primary" @click="logout">退出登录</el-button>
      </div>
    </el-header>

    <el-container style="height: calc(100vh - 60px);">
      <!-- 左侧菜单 -->
      <el-aside width="200px" class="aside">
        <el-menu
          :default-active="activeMenu"
          class="el-menu-vertical-demo"
          @select="handleMenuSelect"
        >
          <!-- 个人中心 -->
          <el-sub-menu index="1">
            <template #title><i class="el-icon-user"></i><span>个人中心</span></template>
            <el-menu-item index="1-1">基本信息</el-menu-item>
          </el-sub-menu>

          <!-- 志愿活动（分角色） -->
          <el-sub-menu index="2">
            <template #title><i class="el-icon-s-data"></i><span>志愿活动</span></template>
            <template v-if="userRole === 'student'">
              <el-menu-item index="2-1">活动列表</el-menu-item>
              <el-menu-item index="2-2">我的报名</el-menu-item>
              <el-menu-item index="2-3">签到打卡</el-menu-item>
              <el-menu-item index="2-4">我的收藏</el-menu-item>
            </template>
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="2-1">发布活动</el-menu-item>
              <el-menu-item index="2-2">活动管理</el-menu-item>
              <el-menu-item index="2-3">报名管理</el-menu-item>
              <el-menu-item index="2-4">签到管理</el-menu-item>
            </template>
          </el-sub-menu>

          <!-- 统计分析（分角色） -->
          <el-sub-menu index="3">
            <template #title><i class="el-icon-chart-pie"></i><span>统计分析</span></template>
            <template v-if="userRole === 'student'">
              <el-menu-item index="3-1">我的时长统计</el-menu-item>
              <el-menu-item index="3-2">违规与申诉</el-menu-item>
            </template>
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="3-1">统计分析</el-menu-item>
              <el-menu-item index="3-2">时长管理</el-menu-item>
              <el-menu-item index="3-3">违规与申诉</el-menu-item>
              <el-menu-item index="3-4">海报生成</el-menu-item>
            </template>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main">
        <el-breadcrumb separator="/" style="margin-bottom: 20px;">
          <el-breadcrumb-item>{{ breadcrumb[0] }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ breadcrumb[1] }}</el-breadcrumb-item>
        </el-breadcrumb>

        <div class="content">
          <!-- 1. 基本信息 -->
          <div v-show="activeMenu === '1-1'">
            <div class="profile-section">
              <!-- 个人信息卡片 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>个人信息</span>
                    <el-button type="primary" size="small" @click="showEditDialog = true">
                      <i class="el-icon-edit"></i> 编辑
                    </el-button>
                  </div>
                </template>
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="用户名">{{ username }}</el-descriptions-item>
                  <el-descriptions-item label="身份">{{ userRole === 'student' ? '学生' : '老师' }}</el-descriptions-item>
                  <el-descriptions-item :label="userRole === 'student' ? '学号' : '工号'">{{ userInfo.idNumber || '暂无' }}</el-descriptions-item>
                  <el-descriptions-item label="手机号">{{ userInfo.phone || '暂无' }}</el-descriptions-item>
                  <el-descriptions-item label="学院">{{ userInfo.college || '暂无' }}</el-descriptions-item>
                  <el-descriptions-item v-if="userRole === 'student'" label="班级">{{ userInfo.classField || '暂无' }}</el-descriptions-item>
                  <el-descriptions-item v-else label="职务">{{ userInfo.class_name || '暂无' }}</el-descriptions-item>
                  <el-descriptions-item label="微信号">{{ userInfo.wechat || '暂无' }}</el-descriptions-item>
                  <el-descriptions-item label="邮箱">{{ userInfo.email || '暂无' }}</el-descriptions-item>
                </el-descriptions>
              </el-card>

              <!-- 学生：志愿数据概览 -->
              <el-card class="stats-card" v-if="userRole === 'student'">
                <template #header>
                  <span>志愿数据概览</span>
                </template>
                <el-row :gutter="20">
                  <el-col :span="6">
                    <div class="stat-item hours">
                      <div class="stat-number">{{ userInfo.totalHours || 0 }}</div>
                      <div class="stat-label">累计时长（小时）</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item activities">
                      <div class="stat-number">{{ userInfo.completedActivities || 0 }}</div>
                      <div class="stat-label">已参与活动</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item pending">
                      <div class="stat-number">{{ userInfo.pendingActivities || 0 }}</div>
                      <div class="stat-label">待参与活动</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item violations">
                      <div class="stat-number">{{ userInfo.violationCount || 0 }}</div>
                      <div class="stat-label">违规次数</div>
                    </div>
                  </el-col>
                </el-row>
              </el-card>

              <!-- 教师：管理数据概览 -->
              <el-card class="stats-card" v-else>
                <template #header>
                  <span>管理数据概览</span>
                </template>
                <el-row :gutter="20">
                  <el-col :span="6">
                    <div class="stat-item activities">
                      <div class="stat-number">{{ teacherStats.publishedActivities || 0 }}</div>
                      <div class="stat-label">发布活动数</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item ongoing">
                      <div class="stat-number">{{ teacherStats.ongoingActivities || 0 }}</div>
                      <div class="stat-label">进行中活动</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item students">
                      <div class="stat-number">{{ teacherStats.totalStudents || 0 }}</div>
                      <div class="stat-label">总参与学生</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item appeals">
                      <div class="stat-number">{{ teacherStats.pendingAppeals || 0 }}</div>
                      <div class="stat-label">待处理申诉</div>
                    </div>
                  </el-col>
                </el-row>
              </el-card>

              <!-- 学生：近期活动提醒 -->
              <el-card class="reminders-card" v-if="userRole === 'student'">
                <template #header>
                  <span>近期活动提醒</span>
                </template>
                <div v-if="recentActivities.length > 0" class="activity-reminders">
                  <div v-for="activity in recentActivities" :key="activity.id" class="reminder-item">
                    <div class="reminder-info">
                      <h4>{{ activity.name }}</h4>
                      <p>时间：{{ formatTime(activity.start_time) }} - {{ formatTime(activity.end_time) }}</p>
                      <p>地点：{{ activity.address }}</p>
                    </div>
                    <el-button 
                      type="primary" 
                      size="small" 
                      @click="handleMenuSelect('2-3')"
                      v-if="!activity.checked_in">
                      前往签到
                    </el-button>
                    <el-tag v-else type="success" size="small">已签到</el-tag>
                  </div>
                </div>
                <el-empty v-else description="暂无近期活动" />
              </el-card>

              <!-- 教师：待办事项 -->
              <el-card class="reminders-card" v-else>
                <template #header>
                  <span>待办事项</span>
                </template>
                <div class="todo-list">
                  <div class="todo-item">
                    <div class="todo-info">
                      <h4>待审核报名</h4>
                      <p>有 {{ teacherStats.pendingApplies || 0 }} 条报名待审核</p>
                    </div>
                    <el-button type="primary" size="small" @click="handleMenuSelect('2-3')">
                      前往审核
                    </el-button>
                  </div>
                  <div class="todo-item">
                    <div class="todo-info">
                      <h4>待处理申诉</h4>
                      <p>有 {{ teacherStats.pendingAppeals || 0 }} 条申诉待处理</p>
                    </div>
                    <el-button type="primary" size="small" @click="handleMenuSelect('3-3')">
                      前往处理
                    </el-button>
                  </div>
                  <div class="todo-item">
                    <div class="todo-info">
                      <h4>进行中活动</h4>
                      <p>有 {{ teacherStats.ongoingActivities || 0 }} 个活动正在进行</p>
                    </div>
                    <el-button type="primary" size="small" @click="handleMenuSelect('2-2')">
                      查看活动
                    </el-button>
                  </div>
                </div>
              </el-card>
            </div>

            <!-- 编辑个人信息对话框 -->
            <el-dialog v-model="showEditDialog" title="编辑个人信息" width="600px">
              <el-form :model="editForm" label-width="100px">
                <el-form-item label="手机号">
                  <el-input v-model="editForm.phone" placeholder="请输入手机号" />
                </el-form-item>
                <el-form-item label="微信号">
                  <el-input v-model="editForm.wechat" placeholder="请输入微信号" />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="editForm.email" placeholder="请输入邮箱" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="showEditDialog = false">取消</el-button>
                <el-button type="primary" @click="saveProfile">保存</el-button>
              </template>
            </el-dialog>
          </div>

          <!-- 学生端：活动列表 -->
          <div v-show="activeMenu === '2-1' && userRole === 'student'">
            <ActivityList />
          </div>

          <!-- 教师端：发布活动 -->
          <div v-show="activeMenu === '2-1' && userRole === 'teacher'">
            <PublishActivity />
          </div>

          <!-- 学生端：我的报名 -->
          <div v-show="activeMenu === '2-2' && userRole === 'student'">
            <MyApplies />
          </div>

          <!-- 教师端：活动管理 -->
          <div v-show="activeMenu === '2-2' && userRole === 'teacher'">
            <ManageActivity />
          </div>

          <!-- 学生端：签到打卡 -->
          <div v-show="activeMenu === '2-3' && userRole === 'student'">
            <CheckIn />
          </div>

          <!-- 教师端：报名管理 -->
          <div v-show="activeMenu === '2-3' && userRole === 'teacher'">
            <ManageApplication />
          </div>

          <!-- 学生端：我的收藏 -->
          <div v-show="activeMenu === '2-4' && userRole === 'student'">
            <MyFavorites />
          </div>

          <!-- 教师端：签到管理 -->
          <div v-show="activeMenu === '2-4' && userRole === 'teacher'">
            <ManageCheckin />
          </div>

          <!-- 学生端：我的时长统计 -->
          <div v-show="activeMenu === '3-1' && userRole === 'student'">
            <HourStats />
          </div>

          <!-- 教师端：统计分析 -->
          <div v-show="activeMenu === '3-1' && userRole === 'teacher'">
            <Statistics />
          </div>

          <!-- 学生端：违规与申诉 -->
          <div v-show="activeMenu === '3-2' && userRole === 'student'">
            <Violations />
          </div>

          <!-- 教师端：时长管理 -->
          <div v-show="activeMenu === '3-2' && userRole === 'teacher'">
            <ManageHours />
          </div>

          <!-- 教师端：违规与申诉 -->
          <div v-show="activeMenu === '3-3' && userRole === 'teacher'">
            <ManageAppeal />
          </div>

          <!-- 教师端：海报生成 -->
          <div v-show="activeMenu === '3-4' && userRole === 'teacher'">
            <Poster />
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { userAPI } from '@/api'
import ActivityList from './ActivityList.vue'
import MyApplies from './MyApplies.vue'
import CheckIn from './CheckIn.vue'
import MyFavorites from './MyFavorites.vue'
import HourStats from './HourStats.vue'
import Violations from './Violations.vue'
import PublishActivity from './PublishActivity.vue'
import ManageActivity from './ManageActivity.vue'
import ManageApplication from './ManageApplication.vue'
import ManageCheckin from './ManageCheckin.vue'
import ManageHours from './ManageHours.vue'
import ManageAppeal from './ManageAppeal.vue'
import Statistics from './Statistics.vue'
import Poster from './Poster.vue'

const router = useRouter()
const username = ref(localStorage.getItem('username') || '未知用户')
const userRole = ref(localStorage.getItem('userRole') || 'student')
const activeMenu = ref('1-1')
const breadcrumb = ref(['个人中心', '基本信息'])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const loading = ref(false)

const userInfo = reactive({
  idNumber: '',
  phone: '',
  college: '',
  classField: '',
  class_name: '',
  wechat: '',
  email: '',
  totalHours: 0,
  completedActivities: 0,
  pendingActivities: 0,
  violationCount: 0
})

const editForm = reactive({
  phone: '',
  wechat: '',
  email: ''
})

const recentActivities = ref([])

// 教师统计数据
const teacherStats = reactive({
  publishedActivities: 0,
  ongoingActivities: 0,
  totalStudents: 0,
  pendingAppeals: 0,
  pendingApplies: 0
})

// 菜单选择逻辑
const handleMenuSelect = (key) => {
  activeMenu.value = key
  const menuMap = {
    '1-1': { name: '基本信息', breadcrumb: ['个人中心', '基本信息'] },
    '2-1': { name: userRole.value === 'student' ? '活动列表' : '发布活动', breadcrumb: ['志愿活动', userRole.value === 'student' ? '活动列表' : '发布活动'] },
    '2-2': { name: userRole.value === 'student' ? '我的报名' : '活动管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '我的报名' : '活动管理'] },
    '2-3': { name: userRole.value === 'student' ? '签到打卡' : '报名管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '签到打卡' : '报名管理'] },
    '2-4': { name: userRole.value === 'student' ? '我的收藏' : '签到管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '我的收藏' : '签到管理'] },
    '3-1': { name: userRole.value === 'student' ? '我的时长统计' : '统计分析', breadcrumb: ['统计分析', userRole.value === 'student' ? '我的时长统计' : '统计分析'] },
    '3-2': { name: userRole.value === 'student' ? '违规与申诉' : '时长管理', breadcrumb: ['统计分析', userRole.value === 'student' ? '违规与申诉' : '时长管理'] },
    '3-3': { name: '违规与申诉', breadcrumb: ['统计分析', '违规与申诉'] },
    '3-4': { name: '海报生成', breadcrumb: ['统计分析', '海报生成'] }
  }
  breadcrumb.value = menuMap[key].breadcrumb
}

// 保存个人信息
const saveProfile = async () => {
  try {
    await userAPI.updateProfile(editForm.value)
    Object.assign(userInfo, editForm.value)
    ElMessage.success('个人信息保存成功')
    showEditDialog.value = false
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 加载近期活动
const loadRecentActivities = async () => {
  try {
    const res = await userAPI.getRecentActivities()
    recentActivities.value = res
  } catch (error) {
    console.error('加载近期活动失败')
  }
}

// 加载教师统计数据
const loadTeacherStats = async () => {
  try {
    const res = await userAPI.getTeacherStats()
    Object.assign(teacherStats, res)
  } catch (error) {
    console.error('加载教师统计数据失败')
  }
}

// 导出证明
const exportCertificate = () => {
  ElMessage.info('导出功能开发中...')
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 退出登录
const logout = () => {
  localStorage.clear()
  ElMessage.success('退出登录成功！')
  router.push('/')
}

// 加载用户信息
onMounted(async () => {
  try {
    loading.value = true
    console.log('开始获取用户信息...')
    console.log('当前 token:', localStorage.getItem('token'))
    const res = await userAPI.getInfo()
    console.log('用户信息获取成功:', res)
    Object.assign(userInfo, res)
    
    // 填充可编辑字段
    editForm.phone = res.phone || ''
    editForm.wechat = res.wechat || ''
    editForm.email = res.email || ''
    
    // 根据角色加载不同数据
    if (userRole.value === 'student') {
      // 加载近期活动
      await loadRecentActivities()
    } else {
      // 加载教师统计数据
      await loadTeacherStats()
    }
  } catch (err) {
    console.error('获取用户信息失败详情:', err)
    console.error('响应数据:', err.response?.data)
    ElMessage.error('获取用户信息失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.admin-layout {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
.header {
  background-color: #fff;
  color: #333;
  line-height: 60px;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #1e73ff;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.aside {
  background-color: #2d3748;
  color: #fff;
}
.el-menu-vertical-demo {
  border-right: none;
  height: 100%;
  background-color: #2d3748;
}

/* 一级菜单样式 */
.el-menu-vertical-demo :deep(.el-sub-menu__title) {
  color: #f7fafc !important;
  font-size: 16px;
  font-weight: 500;
}

/* 一级菜单折叠箭头 */
.el-menu-vertical-demo :deep(.el-sub-menu__title .el-sub-menu__icon-arrow) {
  color: #9ca3af !important;
}

/* 二级菜单样式 - 未选中 */
.el-menu-vertical-demo :deep(.el-menu-item) {
  color: #e2e8f0 !important;
  font-size: 14px;
}

/* 菜单项hover效果 */
.el-menu-vertical-demo :deep(.el-sub-menu__title:hover) {
  background-color: #4a5568 !important;
  color: #ffffff !important;
}

.el-menu-vertical-demo :deep(.el-menu-item:hover) {
  background-color: #4a5568 !important;
  color: #ffffff !important;
}

/* 激活状态 */
.el-menu-vertical-demo :deep(.el-menu-item.is-active) {
  color: #ffffff !important;
  background-color: #1677ff !important;
}

/* 确保所有文字清晰可辨 */
.el-menu-vertical-demo :deep(.el-sub-menu__title),
.el-menu-vertical-demo :deep(.el-menu-item) {
  text-shadow: none;
  opacity: 1;
}
.main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
.content {
  background-color: #fff;
  padding: 20px;
  border-radius: 4px;
  min-height: calc(100% - 40px);
}

/* 个人信息页面样式 */
.profile-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.stats-card {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  transition: all 0.3s ease;
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  background-color: #e9ecef;
}

.stat-item.hours,
.stat-item.activities,
.stat-item.pending,
.stat-item.violations,
.stat-item.ongoing,
.stat-item.students,
.stat-item.appeals {
  background-color: #f5f7fa;
  color: #333;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #1677ff;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.reminders-card {
  margin-bottom: 20px;
}

.activity-reminders {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.reminder-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #1677ff;
}

.reminder-info h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.reminder-info p {
  margin: 4px 0;
  color: #666;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 待办事项样式 */
.todo-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #1677ff;
}

.todo-info h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.todo-info p {
  margin: 4px 0;
  color: #666;
  font-size: 14px;
}
</style>
