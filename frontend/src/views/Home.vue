<template>
  <div class="admin-layout">
    <!-- 顶部导航 -->
    <el-header class="header">
      <div class="header-left">
        <h2>校园志愿服务管理系统</h2>
      </div>
      <div class="header-right">
        <!-- 消息图标 -->
        <el-badge :value="unreadCount" class="message-icon">
          <el-icon size="20"><Bell /></el-icon>
        </el-badge>

        <!-- 当前身份标签 -->
        <el-tag size="small" type="primary">
          角色：{{ userRole === 'student' ? '学生' : '老师' }}
        </el-tag>

        <!-- 用户信息下拉 -->
        <el-dropdown trigger="hover" @command="handleUserCommand">
          <span class="user-info">
            <el-avatar icon="el-icon-user" size="small"></el-avatar>
            {{ username }}
          </span>
          <el-dropdown-menu slot="dropdown">
            <div class="user-card">
              <div class="card-header">
                <el-avatar icon="el-icon-user" size="large"></el-avatar>
                <div class="user-info-card">
                  <p class="name">{{ username }}</p>
                  <p class="role">{{ userRole === 'student' ? '学生' : '老师' }}</p>
                </div>
              </div>
              <el-divider />
              <el-dropdown-item command="changeRole">切换身份</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </div>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </el-header>

    <el-container style="height: calc(100vh - 60px);">
      <!-- 左侧菜单（分角色） -->
      <el-aside width="200px" class="aside">
        <el-menu
          default-active="1-1"
          class="el-menu-vertical-demo"
          @select="handleMenuSelect"
        >
          <!-- 个人中心（所有角色都有） -->
          <el-submenu index="1">
            <template slot="title">
              <i class="el-icon-user"></i>
              <span>个人中心</span>
            </template>
            <el-menu-item index="1-1">基本信息</el-menu-item>
          </el-submenu>

          <!-- 志愿活动（分角色） -->
          <el-submenu index="2">
            <template slot="title">
              <i class="el-icon-s-data"></i>
              <span>志愿活动</span>
            </template>
            <!-- 学生菜单 -->
            <template v-if="userRole === 'student'">
              <el-menu-item index="2-1">活动列表</el-menu-item>
              <el-menu-item index="2-2">我的报名</el-menu-item>
              <el-menu-item index="2-3">活动记录</el-menu-item>
            </template>
            <!-- 老师菜单 -->
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="2-1">活动管理</el-menu-item>
              <el-menu-item index="2-2">报名管理</el-menu-item>
            </template>
          </el-submenu>

          <!-- 考勤管理（分角色） -->
          <el-submenu index="3">
            <template slot="title">
              <i class="el-icon-time"></i>
              <span>考勤管理</span>
            </template>
            <template v-if="userRole === 'student'">
              <el-menu-item index="3-1">签到打卡</el-menu-item>
              <el-menu-item index="3-2">我的考勤记录</el-menu-item>
            </template>
            <template v-if="userRole === 'teacher'">
              <el-menu-item index="3-1">活动考勤管理</el-menu-item>
              <el-menu-item index="3-2">考勤导出</el-menu-item>
            </template>
          </el-submenu>

          <!-- 消息通知（分角色） -->
          <el-submenu index="4">
            <template slot="title">
              <i class="el-icon-bell"></i>
              <span>消息通知</span>
            </template>
            <el-menu-item index="4-1">系统通知</el-menu-item>
            <el-menu-item index="4-2">我的消息</el-menu-item>
            <!-- 老师专属：发布通知 -->
            <el-menu-item index="4-3" v-if="userRole === 'teacher'">发布通知</el-menu-item>
          </el-submenu>

          <!-- 统计分析（分角色） -->
          <el-submenu index="5">
            <template slot="title">
              <i class="el-icon-chart-pie"></i>
              <span>统计分析</span>
            </template>
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

      <!-- 中间内容区 -->
      <el-main class="main">
        <el-breadcrumb separator="/" style="margin-bottom: 20px;">
          <el-breadcrumb-item>{{ breadcrumb[0] }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ breadcrumb[1] }}</el-breadcrumb-item>
        </el-breadcrumb>

        <div class="content">
          <!-- 基本信息（含密码修改） -->
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

            <!-- 密码修改卡片（折叠） -->
            <el-card title="密码修改" style="margin-top: 20px;">
              <el-collapse v-model="collapseActive">
                <el-collapse-item title="点击展开修改密码" name="1">
                  <el-form label-width="80px" @submit.prevent="changePwd">
                    <el-form-item label="原密码">
                      <el-input v-model="pwdForm.oldPwd" type="password"></el-input>
                    </el-form-item>
                    <el-form-item label="新密码">
                      <el-input v-model="pwdForm.newPwd" type="password"></el-input>
                    </el-form-item>
                    <el-form-item label="确认新密码">
                      <el-input v-model="pwdForm.confirmPwd" type="password"></el-input>
                    </el-form-item>
                    <el-form-item>
                      <el-button type="primary" native-type="submit">提交修改</el-button>
                    </el-form-item>
                  </el-form>
                </el-collapse-item>
              </el-collapse>
            </el-card>
          </div>

          <!-- 学生-活动列表 -->
          <div v-if="activeMenu === '2-1' && userRole === 'student'">
            <el-card title="志愿活动列表">
              <el-input placeholder="搜索活动名称" style="width: 300px; margin-bottom: 20px;"></el-input>
              <el-table :data="studentActivityList" border>
                <el-table-column prop="name" label="活动名称" />
                <el-table-column prop="time" label="活动时间" />
                <el-table-column prop="address" label="活动地点" />
                <el-table-column prop="quota" label="剩余名额" />
                <el-table-column label="操作">
                  <template slot-scope="scope">
                    <el-button type="primary" size="mini" @click="applyActivity(scope.row)">报名</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- 老师-活动管理 -->
          <div v-if="activeMenu === '2-1' && userRole === 'teacher'">
            <el-card title="活动管理">
              <el-button type="primary" style="margin-bottom: 20px;">发布新活动</el-button>
              <el-table :data="teacherActivityList" border>
                <el-table-column prop="name" label="活动名称" />
                <el-table-column prop="time" label="活动时间" />
                <el-table-column prop="address" label="活动地点" />
                <el-table-column prop="applyCount" label="报名人数" />
                <el-table-column label="操作">
                  <template slot-scope="scope">
                    <el-button size="mini">编辑</el-button>
                    <el-button size="mini" type="danger">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- 其他页面占位 -->
          <div v-else>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Bell } from '@element-plus/icons-vue'

const router = useRouter()

// 基础信息
const username = ref(localStorage.username || '未知用户')
const userRole = ref(localStorage.userRole || 'student')
const unreadCount = ref(3) // 未读消息数
const collapseActive = ref([]) // 密码修改折叠面板

// 面包屑+菜单
const breadcrumb = ref(['个人中心', '基本信息'])
const activeMenu = ref('1-1')
const currentMenuName = ref('基本信息')

// 用户信息
const userInfo = reactive({
  idNumber: '',
  phone: '',
  totalHours: 0,
  class: ''
})

// 密码修改表单
const pwdForm = reactive({
  oldPwd: '',
  newPwd: '',
  confirmPwd: ''
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

// 菜单选择
const handleMenuSelect = (key) => {
  activeMenu.value = key
  const menuMap = {
    // 个人中心
    '1-1': { name: '基本信息', breadcrumb: ['个人中心', '基本信息'] },
    // 学生-志愿活动
    '2-1': { name: '活动列表', breadcrumb: ['志愿活动', '活动列表'] },
    '2-2': { name: '我的报名', breadcrumb: ['志愿活动', '我的报名'] },
    '2-3': { name: '活动记录', breadcrumb: ['志愿活动', '活动记录'] },
    // 老师-志愿活动
    '2-1': { name: '活动管理', breadcrumb: ['志愿活动', '活动管理'] },
    '2-2': { name: '报名管理', breadcrumb: ['志愿活动', '报名管理'] },
    // 考勤管理
    '3-1': { name: userRole.value === 'student' ? '签到打卡' : '活动考勤管理', breadcrumb: ['考勤管理', userRole.value === 'student' ? '签到打卡' : '活动考勤管理'] },
    '3-2': { name: userRole.value === 'student' ? '我的考勤记录' : '考勤导出', breadcrumb: ['考勤管理', userRole.value === 'student' ? '我的考勤记录' : '考勤导出'] },
    // 消息通知
    '4-1': { name: '系统通知', breadcrumb: ['消息通知', '系统通知'] },
    '4-2': { name: '我的消息', breadcrumb: ['消息通知', '我的消息'] },
    '4-3': { name: '发布通知', breadcrumb: ['消息通知', '发布通知'] },
    // 统计分析
    '5-1': { name: userRole.value === 'student' ? '我的时长统计' : '全院时长统计', breadcrumb: ['统计分析', userRole.value === 'student' ? '我的时长统计' : '全院时长统计'] },
    '5-2': { name: userRole.value === 'student' ? '参与活动统计' : '活动参与率统计', breadcrumb: ['统计分析', userRole.value === 'student' ? '参与活动统计' : '活动参与率统计'] }
  }
  currentMenuName.value = menuMap[key].name
  breadcrumb.value = menuMap[key].breadcrumb
}

// 用户下拉菜单操作
const handleUserCommand = (command) => {
  if (command === 'changeRole') {
    // 切换身份：弹出选择框
    ElMessageBox.confirm(
      '请选择要切换的身份',
      '切换身份',
      {
        confirmButtonText: '学生',
        cancelButtonText: '老师',
        type: 'info'
      }
    ).then(() => {
      if (userRole.value === 'student') {
        ElMessage.info('当前已是学生身份，无需切换')
      } else {
        // 切换为学生：更新本地存储+刷新
        localStorage.userRole = 'student'
        userRole.value = 'student'
        ElMessage.success('已切换为学生身份')
        window.location.reload()
      }
    }).catch(() => {
      if (userRole.value === 'teacher') {
        ElMessage.info('当前已是老师身份，无需切换')
      } else {
        // 切换为老师：更新本地存储+刷新
        localStorage.userRole = 'teacher'
        userRole.value = 'teacher'
        ElMessage.success('已切换为老师身份')
        window.location.reload()
      }
    })
  } else if (command === 'logout') {
    // 退出登录
    localStorage.clear()
    ElMessage.success('退出登录成功')
    router.push('/')
  }
}

// 密码修改
const changePwd = async () => {
  if (!pwdForm.oldPwd || !pwdForm.newPwd || !pwdForm.confirmPwd) {
    ElMessage.warning('请填写所有字段！')
    return
  }
  if (pwdForm.newPwd !== pwdForm.confirmPwd) {
    ElMessage.error('两次密码输入不一致！')
    return
  }
  try {
    await axios.post('/api/user/changePwd', {
      oldPwd: pwdForm.oldPwd,
      newPwd: pwdForm.newPwd
    })
    ElMessage.success('密码修改成功，请重新登录！')
    localStorage.clear()
    router.push('/')
  } catch (err) {
    ElMessage.error(err.response?.data?.msg || '密码修改失败')
  }
}

// 学生报名活动
const applyActivity = (row) => {
  ElMessageBox.confirm(
    `是否报名「${row.name}」？`,
    '报名确认',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消'
    }
  ).then(() => {
    ElMessage.success('报名成功！')
    row.quota -= 1
  })
}

// 加载用户信息
onMounted(async () => {
  try {
    const res = await axios.get('/api/user/info', {
      headers: { Authorization: `Bearer ${localStorage.token}` }
    })
    Object.assign(userInfo, res.data)
  } catch (err) {
    ElMessage.error('获取用户信息失败')
    localStorage.clear()
    router.push('/')
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
.message-icon {
  cursor: pointer;
}
.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-card {
  width: 200px;
  padding: 10px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.user-info-card .name {
  font-weight: 500;
  margin: 0;
}
.user-info-card .role {
  font-size: 12px;
  color: #666;
  margin: 0;
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