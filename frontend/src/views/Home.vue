<template>
  <div class="admin-layout">
    <!-- 顶部导航栏 -->
    <el-header class="header">
      <div class="header-left">
        <h2>校园志愿服务管理系统</h2>
      </div>
      <div class="header-right">
        <el-dropdown>
          <span class="user-info">
            <el-avatar icon="el-icon-user" size="small"></el-avatar>
            {{ userInfo.username }}
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item @click="goToProfile">个人中心</el-dropdown-item>
            <el-dropdown-item @click="changeRole">切换身份</el-dropdown-item>
            <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </el-header>

    <el-container style="height: calc(100vh - 60px);">
      <!-- 左侧菜单栏 -->
      <el-aside width="200px" class="aside">
        <el-menu
          default-active="1-1"
          class="el-menu-vertical-demo"
          @select="handleMenuSelect"
        >
          <!-- 个人中心 -->
          <el-submenu index="1">
            <template slot="title">
              <i class="el-icon-user"></i>
              <span>个人中心</span>
            </template>
            <el-menu-item index="1-1">基本信息</el-menu-item>
            <el-menu-item index="1-2">密码修改</el-menu-item>
          </el-submenu>

          <!-- 志愿活动 -->
          <el-submenu index="2">
            <template slot="title">
              <i class="el-icon-s-data"></i>
              <span>志愿活动</span>
            </template>
            <el-menu-item index="2-1">活动列表</el-menu-item>
            <el-menu-item index="2-2">我的报名</el-menu-item>
            <el-menu-item index="2-3">活动记录</el-menu-item>
          </el-submenu>

          <!-- 荣誉管理 -->
          <el-submenu index="3">
            <template slot="title">
              <i class="el-icon-medal"></i>
              <span>荣誉管理</span>
            </template>
            <el-menu-item index="3-1">荣誉称号申请</el-menu-item>
            <el-menu-item index="3-2">我的荣誉</el-menu-item>
          </el-submenu>

          <!-- 考勤管理 -->
          <el-submenu index="4">
            <template slot="title">
              <i class="el-icon-time"></i>
              <span>考勤管理</span>
            </template>
            <el-menu-item index="4-1">签到打卡</el-menu-item>
            <el-menu-item index="4-2">考勤记录</el-menu-item>
          </el-submenu>

          <!-- 消息通知 -->
          <el-submenu index="5">
            <template slot="title">
              <i class="el-icon-bell"></i>
              <span>消息通知</span>
            </template>
            <el-menu-item index="5-1">系统通知</el-menu-item>
            <el-menu-item index="5-2">我的消息</el-menu-item>
          </el-submenu>

          <!-- 统计分析 -->
          <el-submenu index="6">
            <template slot="title">
              <i class="el-icon-chart-pie"></i>
              <span>统计分析</span>
            </template>
            <el-menu-item index="6-1">时长统计</el-menu-item>
            <el-menu-item index="6-2">活动统计</el-menu-item>
          </el-submenu>
        </el-menu>
      </el-aside>

      <!-- 中间内容区 -->
      <el-main class="main">
        <!-- 面包屑导航 -->
        <el-breadcrumb separator="/" style="margin-bottom: 20px;">
          <el-breadcrumb-item>{{ breadcrumb[0] }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ breadcrumb[1] }}</el-breadcrumb-item>
        </el-breadcrumb>

        <!-- 动态内容区域 -->
        <div class="content">
          <!-- 基本信息 -->
          <div v-if="activeMenu === '1-1'">
            <el-card title="个人基本信息">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="用户名">{{ userInfo.username }}</el-descriptions-item>
                <el-descriptions-item label="学号">{{ userInfo.student_id }}</el-descriptions-item>
                <el-descriptions-item label="手机号">{{ userInfo.phone }}</el-descriptions-item>
                <el-descriptions-item label="累计志愿时长">{{ userInfo.total_hours || 0 }} 小时</el-descriptions-item>
                <el-descriptions-item label="身份">{{ userInfo.role || '学生' }}</el-descriptions-item>
                <el-descriptions-item label="注册时间">{{ userInfo.register_time || '2026-03-01' }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>

          <!-- 密码修改 -->
          <div v-if="activeMenu === '1-2'">
            <el-card title="修改密码">
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
            </el-card>
          </div>

          <!-- 荣誉称号申请 -->
          <div v-if="activeMenu === '3-1'">
            <el-card>
              <!-- 搜索栏 -->
              <div class="search-bar" style="margin-bottom: 20px;">
                <el-input v-model="honorName" placeholder="荣誉称号名称" style="width: 200px; margin-right: 10px;"></el-input>
                <el-button type="primary">查询</el-button>
                <el-button type="primary" style="margin-left: 10px; background: #409eff;">申请</el-button>
                <el-button type="danger">删除</el-button>
              </div>

              <!-- 表格 -->
              <el-table :data="honorList" border style="width: 100%;">
                <el-table-column type="selection" width="55"></el-table-column>
                <el-table-column prop="student_id" label="学号"></el-table-column>
                <el-table-column prop="name" label="姓名"></el-table-column>
                <el-table-column prop="college" label="学院"></el-table-column>
                <el-table-column prop="school_year" label="学年"></el-table-column>
                <el-table-column prop="honor_name" label="荣誉称号名称"></el-table-column>
                <el-table-column prop="plan_name" label="方案名称"></el-table-column>
                <el-table-column prop="honor_type" label="荣誉称号类别"></el-table-column>
                <el-table-column prop="honor_level" label="荣誉称号级别"></el-table-column>
                <el-table-column prop="audit_status" label="审核状态"></el-table-column>
                <el-table-column label="操作">
                  <template slot-scope="scope">
                    <el-button size="mini">编辑</el-button>
                    <el-button size="mini" type="danger">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 分页 -->
              <el-pagination
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
                :current-page="currentPage"
                :page-sizes="[10, 20, 50, 100]"
                :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="total"
                style="margin-top: 20px; text-align: right;"
              >
              </el-pagination>
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

const router = useRouter()

// 用户信息
const userInfo = reactive({
  username: localStorage.username || '钟雪怡',
  student_id: '2022463012345',
  phone: '13800138000',
  role: '学生'
})

// 面包屑导航
const breadcrumb = ref(['个人中心', '基本信息'])

// 激活的菜单
const activeMenu = ref('1-1')
// 当前菜单名称
const currentMenuName = ref('基本信息')

// 密码修改表单
const pwdForm = reactive({
  oldPwd: '',
  newPwd: '',
  confirmPwd: ''
})

// 荣誉申请相关
const honorName = ref('')
const honorList = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 菜单选择事件
const handleMenuSelect = (key) => {
  activeMenu.value = key
  // 映射菜单名称和面包屑
  const menuMap = {
    '1-1': { name: '基本信息', breadcrumb: ['个人中心', '基本信息'] },
    '1-2': { name: '密码修改', breadcrumb: ['个人中心', '密码修改'] },
    '2-1': { name: '活动列表', breadcrumb: ['志愿活动', '活动列表'] },
    '2-2': { name: '我的报名', breadcrumb: ['志愿活动', '我的报名'] },
    '2-3': { name: '活动记录', breadcrumb: ['志愿活动', '活动记录'] },
    '3-1': { name: '荣誉称号申请', breadcrumb: ['荣誉管理', '荣誉称号申请'] },
    '3-2': { name: '我的荣誉', breadcrumb: ['荣誉管理', '我的荣誉'] },
    '4-1': { name: '签到打卡', breadcrumb: ['考勤管理', '签到打卡'] },
    '4-2': { name: '考勤记录', breadcrumb: ['考勤管理', '考勤记录'] },
    '5-1': { name: '系统通知', breadcrumb: ['消息通知', '系统通知'] },
    '5-2': { name: '我的消息', breadcrumb: ['消息通知', '我的消息'] },
    '6-1': { name: '时长统计', breadcrumb: ['统计分析', '时长统计'] },
    '6-2': { name: '活动统计', breadcrumb: ['统计分析', '活动统计'] }
  }
  currentMenuName.value = menuMap[key].name
  breadcrumb.value = menuMap[key].breadcrumb
}

// 密码修改
const changePwd = () => {
  if (!pwdForm.oldPwd || !pwdForm.newPwd || !pwdForm.confirmPwd) {
    ElMessage.warning('请填写所有字段')
    return
  }
  if (pwdForm.newPwd !== pwdForm.confirmPwd) {
    ElMessage.error('两次密码输入不一致')
    return
  }
  ElMessage.success('密码修改成功，请重新登录')
  logout()
}

// 切换身份
const changeRole = () => {
  ElMessageBox.confirm(
    '请选择要切换的身份',
    '切换身份',
    {
      confirmButtonText: '管理员',
      cancelButtonText: '志愿者队长',
      type: 'info'
    }
  ).then(() => {
    userInfo.role = '管理员'
    ElMessage.success('已切换为管理员身份')
  }).catch(() => {
    userInfo.role = '志愿者队长'
    ElMessage.success('已切换为志愿者队长身份')
  })
}

// 退出登录
const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  ElMessage.success('退出登录成功')
  router.push('/')
}

// 跳转到个人中心
const goToProfile = () => {
  activeMenu.value = '1-1'
  handleMenuSelect('1-1')
}

// 分页事件
const handleSizeChange = (val) => {
  pageSize.value = val
}
const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 页面加载时获取用户信息
onMounted(async () => {
  try {
    const res = await axios.get('/api/user/info/')
    Object.assign(userInfo, res.data)
    localStorage.username = res.data.username
  } catch (e) {
    ElMessage.error('获取用户信息失败')
    logout()
  }
})
</script>

<style scoped>
/* 整体布局 */
.admin-layout {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

/* 顶部导航 */
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

.header-right .user-info {
  cursor: pointer;
  margin-right: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 左侧菜单 */
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

/* 中间内容区 */
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

/* 搜索栏 */
.search-bar {
  display: flex;
  align-items: center;
}
</style>