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
          <!-- 志愿活动（分角色） -->
          <el-sub-menu index="2">
            <template #title><i class="el-icon-s-data"></i><span>志愿活动</span></template>
            <template v-if="userRole === 'student'">
              <el-menu-item index="2-1">活动列表</el-menu-item>
              <el-menu-item index="2-2">我的报名</el-menu-item>
              <el-menu-item index="2-3">我的收藏</el-menu-item>
              <el-menu-item index="2-4">签到打卡</el-menu-item>
            </template>
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="2-1">活动管理</el-menu-item>
              <el-menu-item index="2-2">报名管理</el-menu-item>
              <el-menu-item index="2-3">违规管理</el-menu-item>
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
              <el-menu-item index="3-1">全院时长统计</el-menu-item>
              <el-menu-item index="3-2">活动参与率统计</el-menu-item>
              <el-menu-item index="3-3">时长导出</el-menu-item>
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
          <div v-if="activeMenu === '1-1'">
            <el-card title="个人基本信息">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="用户名">{{ username }}</el-descriptions-item>
                <el-descriptions-item label="身份">{{ userRole === 'student' ? '学生' : '老师' }}</el-descriptions-item>
                <el-descriptions-item label="学号/工号">{{ userInfo.idNumber || '暂无' }}</el-descriptions-item>
                <el-descriptions-item label="手机号">{{ userInfo.phone || '暂无' }}</el-descriptions-item>
                <el-descriptions-item label="累计志愿时长" v-if="userRole === 'student'">
                  {{ userInfo.totalHours || 0 }} 小时
                </el-descriptions-item>
                <el-descriptions-item label="负责班级" v-if="userRole === 'teacher'">
                  {{ userInfo.classField || '暂无' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>

          <!-- 2. 学生-活动列表 -->
          <div v-if="activeMenu === '2-1' && userRole === 'student'">
            <el-card title="志愿活动列表">
              <el-button type="primary" @click="$router.push('/activities')">查看所有活动</el-button>
              <p style="margin-top: 20px; color: #666;">点击按钮查看所有可报名的志愿活动</p>
            </el-card>
          </div>

          <!-- 2. 老师-活动管理 -->
          <div v-if="activeMenu === '2-1' && userRole === 'teacher'">
            <el-card title="活动管理">
              <el-button type="primary" @click="showCreateDialog = true">发布新活动</el-button>
              <p style="margin-top: 20px; color: #666;">点击按钮发布新的志愿活动</p>
            </el-card>
          </div>

          <!-- 2. 学生-我的报名 -->
          <div v-if="activeMenu === '2-2' && userRole === 'student'">
            <el-card title="我的报名记录">
              <el-button type="primary" @click="$router.push('/activities')">查看我的报名</el-button>
              <p style="margin-top: 20px; color: #666;">点击按钮查看您的报名记录</p>
            </el-card>
          </div>

          <!-- 2. 老师-报名管理 -->
          <div v-if="activeMenu === '2-2' && userRole === 'teacher'">
            <el-card title="报名管理">
              <p style="color: #666;">管理学生报名申请</p>
            </el-card>
          </div>

          <!-- 2. 学生-签到打卡 -->
          <div v-if="activeMenu === '2-3' && userRole === 'student'">
            <el-card title="签到打卡">
              <el-button type="primary" @click="$router.push('/checkin')">前往签到</el-button>
              <p style="margin-top: 20px; color: #666;">点击按钮进行活动签到</p>
            </el-card>
          </div>

          <!-- 2. 老师-违规管理 -->
          <div v-if="activeMenu === '2-3' && userRole === 'teacher'">
            <el-card title="违规管理">
              <p style="color: #666;">管理学生违规记录</p>
            </el-card>
          </div>

          <!-- 3. 学生-时长统计 -->
          <div v-if="activeMenu === '3-1' && userRole === 'student'">
            <el-card title="我的时长统计">
              <el-button type="primary" @click="$router.push('/stats')">查看详细统计</el-button>
              <p style="margin-top: 20px; color: #666;">点击按钮查看您的志愿时长统计</p>
            </el-card>
          </div>

          <!-- 3. 老师-全院时长统计 -->
          <div v-if="activeMenu === '3-1' && userRole === 'teacher'">
            <el-card title="全院时长统计">
              <p style="color: #666;">查看全院学生志愿时长统计</p>
            </el-card>
          </div>

          <!-- 3. 学生-违规记录 -->
          <div v-if="activeMenu === '3-2' && userRole === 'student'">
            <el-card title="违规记录">
              <p style="color: #666;">查看您的违规记录</p>
            </el-card>
          </div>

          <!-- 3. 老师-活动参与率统计 -->
          <div v-if="activeMenu === '3-2' && userRole === 'teacher'">
            <el-card title="活动参与率统计">
              <p style="color: #666;">查看活动参与率统计</p>
            </el-card>
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

const router = useRouter()
const username = ref(localStorage.getItem('username') || '未知用户')
const userRole = ref(localStorage.getItem('userRole') || 'student')
const activeMenu = ref('1-1')
const breadcrumb = ref(['个人中心', '基本信息'])
const showCreateDialog = ref(false)

const userInfo = reactive({
  idNumber: '',
  phone: '',
  totalHours: 0,
  classField: ''
})

// 菜单选择逻辑
const handleMenuSelect = (key) => {
  activeMenu.value = key
  const menuMap = {
    '1-1': { name: '基本信息', breadcrumb: ['个人中心', '基本信息'] },
    '2-1': { name: userRole.value === 'student' ? '活动列表' : '活动管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '活动列表' : '活动管理'] },
    '2-2': { name: userRole.value === 'student' ? '我的报名' : '报名管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '我的报名' : '报名管理'] },
    '2-3': { name: userRole.value === 'student' ? '签到打卡' : '违规管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '签到打卡' : '违规管理'] },
    '3-1': { name: userRole.value === 'student' ? '我的时长统计' : '全院时长统计', breadcrumb: ['统计分析', userRole.value === 'student' ? '我的时长统计' : '全院时长统计'] },
    '3-2': { name: userRole.value === 'student' ? '违规记录' : '活动参与率统计', breadcrumb: ['统计分析', userRole.value === 'student' ? '违规记录' : '活动参与率统计'] }
  }
  breadcrumb.value = menuMap[key].breadcrumb
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
    console.log('开始获取用户信息...')
    console.log('当前 token:', localStorage.getItem('token'))
    const res = await userAPI.getInfo()
    console.log('用户信息获取成功:', res)
    Object.assign(userInfo, res)
  } catch (err) {
    console.error('获取用户信息失败详情:', err)
    console.error('响应数据:', err.response?.data)
    ElMessage.error('获取用户信息失败')
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
  background-color: #2e3b4e;
  color: #fff;
}
.el-menu-vertical-demo {
  border-right: none;
  height: 100%;
  background-color: #2e3b4e;
}
.el-menu-vertical-demo .el-submenu__title {
  color: #fff;
}
.el-menu-vertical-demo .el-menu-item {
  color: #ccc;
}
.el-menu-vertical-demo .el-menu-item.is-active {
  color: #fff;
  background-color: #1e73ff;
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
</style>