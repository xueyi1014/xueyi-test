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
        <el-button size="small" type="text" @click="logout">退出登录</el-button>
      </div>
    </el-header>

    <el-container style="height: calc(100vh - 60px);">
      <!-- 左侧菜单 -->
      <el-aside width="200px" class="aside">
        <el-menu
          default-active="1-1"
          class="el-menu-vertical-demo"
          @select="handleMenuSelect"
        >
          <!-- 个人中心 -->
          <el-submenu index="1">
            <template slot="title"><i class="el-icon-user"></i><span>个人中心</span></template>
            <el-menu-item index="1-1">基本信息</el-menu-item>
          </el-submenu>

          <!-- 志愿活动（分角色） -->
          <el-submenu index="2">
            <template slot="title"><i class="el-icon-s-data"></i><span>志愿活动</span></template>
            <template v-if="userRole === 'student'">
              <el-menu-item index="2-1">活动列表</el-menu-item>
              <el-menu-item index="2-2">我的报名</el-menu-item>
              <el-menu-item index="2-3">活动记录</el-menu-item>
            </template>
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="2-1">活动管理</el-menu-item>
              <el-menu-item index="2-2">报名管理</el-menu-item>
            </template>
          </el-submenu>

          <!-- 考勤管理（分角色） -->
          <el-submenu index="3">
            <template slot="title"><i class="el-icon-time"></i><span>考勤管理</span></template>
            <template v-if="userRole === 'student'">
              <el-menu-item index="3-1">签到打卡</el-menu-item>
              <el-menu-item index="3-2">我的考勤记录</el-menu-item>
            </template>
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="3-1">活动考勤管理</el-menu-item>
              <el-menu-item index="3-2">考勤导出</el-menu-item>
            </template>
          </el-submenu>

          <!-- 统计分析（分角色） -->
          <el-submenu index="5">
            <template slot="title"><i class="el-icon-chart-pie"></i><span>统计分析</span></template>
            <template v-if="userRole === 'student'">
              <el-menu-item index="5-1">我的时长统计</el-menu-item>
              <el-menu-item index="5-2">参与活动统计</el-menu-item>
            </template>
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="5-1">全院时长统计</el-menu-item>
              <el-menu-item index="5-2">活动参与率统计</el-menu-item>
            </template>
          </el-submenu>
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
                  {{ userInfo.class || '暂无' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>

          <!-- 2. 学生-活动列表 -->
          <div v-if="activeMenu === '2-1' && userRole === 'student'">
            <el-card title="志愿活动列表">
              <el-input placeholder="搜索活动名称" style="width: 300px; margin-bottom: 20px;"></el-input>
              <el-table :data="studentActivityList" border>
                <el-table-column prop="name" label="活动名称" />
                <el-table-column prop="time" label="活动时间" />
                <el-table-column prop="address" label="活动地点" />
                <el-table-column prop="quota" label="剩余名额" />
                <el-table-column label="操作">
                  <template #default="scope">
                    <el-button type="primary" size="mini" @click="applyActivity(scope.row)">报名</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- 3. 老师-活动管理 -->
          <div v-if="activeMenu === '2-1' && userRole === 'teacher'">
            <el-card title="活动管理">
              <el-button type="primary" style="margin-bottom: 20px;">发布新活动</el-button>
              <el-table :data="teacherActivityList" border>
                <el-table-column prop="name" label="活动名称" />
                <el-table-column prop="time" label="活动时间" />
                <el-table-column prop="address" label="活动地点" />
                <el-table-column prop="applyCount" label="报名人数" />
                <el-table-column label="操作">
                  <template #default="scope">
                    <el-button size="mini">编辑</el-button>
                    <el-button size="mini" type="danger">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- 4. 其他页面占位 -->
          <div v-else-if="activeMenu !== '1-1'">
            <el-card>
              <h3>{{ currentMenuName }}</h3>
              <p>该模块功能正在开发中...</p>
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
import request from '@/utils/request'

const router = useRouter()
const username = ref(localStorage.getItem('username') || '未知用户')
const userRole = ref(localStorage.getItem('userRole') || 'student')
const activeMenu = ref('1-1')
const breadcrumb = ref(['个人中心', '基本信息'])
const currentMenuName = ref('基本信息')

const userInfo = reactive({
  idNumber: '',
  phone: '',
  totalHours: 0,
  class: ''
})

// 模拟数据
const studentActivityList = ref([
  { name: '校园清洁志愿活动', time: '2026-04-01 09:00', address: '学校操场', quota: 15 },
  { name: '社区敬老服务', time: '2026-04-05 14:00', address: '幸福社区', quota: 8 }
])
const teacherActivityList = ref([
  { name: '校园清洁志愿活动', time: '2026-04-01 09:00', address: '学校操场', applyCount: 25 },
  { name: '社区敬老服务', time: '2026-04-05 14:00', address: '幸福社区', applyCount: 12 }
])

// 菜单选择逻辑
const handleMenuSelect = (key) => {
  activeMenu.value = key
  const menuMap = {
    '1-1': { name: '基本信息', breadcrumb: ['个人中心', '基本信息'] },
    '2-1': { name: userRole.value === 'student' ? '活动列表' : '活动管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '活动列表' : '活动管理'] },
    '2-2': { name: userRole.value === 'student' ? '我的报名' : '报名管理', breadcrumb: ['志愿活动', userRole.value === 'student' ? '我的报名' : '报名管理'] },
    '2-3': { name: '活动记录', breadcrumb: ['志愿活动', '活动记录'] },
    '3-1': { name: userRole.value === 'student' ? '签到打卡' : '活动考勤管理', breadcrumb: ['考勤管理', userRole.value === 'student' ? '签到打卡' : '活动考勤管理'] },
    '3-2': { name: userRole.value === 'student' ? '我的考勤记录' : '考勤导出', breadcrumb: ['考勤管理', userRole.value === 'student' ? '我的考勤记录' : '考勤导出'] },
    '5-1': { name: userRole.value === 'student' ? '我的时长统计' : '全院时长统计', breadcrumb: ['统计分析', userRole.value === 'student' ? '我的时长统计' : '全院时长统计'] },
    '5-2': { name: userRole.value === 'student' ? '参与活动统计' : '活动参与率统计', breadcrumb: ['统计分析', userRole.value === 'student' ? '参与活动统计' : '活动参与率统计'] }
  }
  currentMenuName.value = menuMap[key].name
  breadcrumb.value = menuMap[key].breadcrumb
}

// 退出登录
const logout = () => {
  localStorage.clear()
  ElMessage.success('退出登录成功！')
  router.push('/')
}

// 报名活动
const applyActivity = (row) => {
  ElMessage.success(`已成功报名「${row.name}」！`)
  row.quota -= 1
}

// 加载用户信息
onMounted(async () => {
  try {
    const res = await request.get('/api/user/info/')
    Object.assign(userInfo, res)
  } catch (err) {
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