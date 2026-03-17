<template>
  <div class="user-center">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个人中心</span>
        </div>
      </template>

      <!-- 基本信息 -->
      <div class="basic-info">
        <h3>基本信息</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ userInfo.username }}</el-descriptions-item>
          <el-descriptions-item label="身份">{{ userRole === 'student' ? '学生' : '老师' }}</el-descriptions-item>
          <el-descriptions-item label="学号/工号">{{ userInfo.idNumber || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ userInfo.phone || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ userInfo.email || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatTime(userInfo.create_time) }}</el-descriptions-item>
          <el-descriptions-item v-if="userRole === 'student'" label="累计志愿时长">
            {{ userInfo.totalHours || 0 }} 小时
          </el-descriptions-item>
          <el-descriptions-item v-if="userRole === 'teacher'" label="负责班级">
            {{ userInfo.classField || '暂无' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 修改密码 -->
      <div class="password-section">
        <el-divider>修改密码</el-divider>
        <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
          <el-form-item label="原密码" prop="oldPassword">
            <el-input v-model="passwordForm.oldPassword" type="password" placeholder="请输入原密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="changePassword">修改密码</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 学生专属：违规记录 -->
      <div v-if="userRole === 'student'" class="violation-section">
        <el-divider>违规记录</el-divider>
        <el-table :data="violationRecords" border style="width: 100%;">
          <el-table-column prop="activity.name" label="活动名称" />
          <el-table-column prop="violation_type" label="违规类型">
            <template #default="{ row }">
              <el-tag :type="getViolationType(row.violation_type)">{{ getViolationText(row.violation_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="违规描述" />
          <el-table-column prop="penalty_hours" label="扣除时长" />
          <el-table-column label="记录时间">
            <template #default="{ row }">
              {{ formatTime(row.create_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_by.username" label="记录人" />
        </el-table>
      </div>

      <!-- 老师专属：管理功能 -->
      <div v-if="userRole === 'teacher'" class="teacher-section">
        <el-divider>管理功能</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card shadow="hover" class="function-card">
              <template #header>
                <div class="function-header">
                  <i class="el-icon-s-management"></i>
                  <span>活动管理</span>
                </div>
              </template>
              <p>管理志愿活动，包括发布、编辑、取消活动</p>
              <el-button type="primary" @click="$router.push('/activities')">进入管理</el-button>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" class="function-card">
              <template #header>
                <div class="function-header">
                  <i class="el-icon-user"></i>
                  <span>报名管理</span>
                </div>
              </template>
              <p>审核学生报名申请，管理报名状态</p>
              <el-button type="primary">进入管理</el-button>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" class="function-card">
              <template #header>
                <div class="function-header">
                  <i class="el-icon-warning"></i>
                  <span>违规管理</span>
                </div>
              </template>
              <p>记录学生违规行为，管理黑名单</p>
              <el-button type="primary">进入管理</el-button>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userAPI, violationAPI } from '@/api'

const userRole = ref(localStorage.getItem('userRole') || 'student')
const userInfo = reactive({
  username: '',
  idNumber: '',
  phone: '',
  email: '',
  totalHours: 0,
  classField: '',
  create_time: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordFormRef = ref()
const violationRecords = ref([])

// 密码验证规则
const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const res = await userAPI.getInfo()
    Object.assign(userInfo, res)
    userInfo.username = localStorage.getItem('username') || res.username
  } catch (error) {
    ElMessage.error('加载用户信息失败')
  }
}

// 加载违规记录（学生）
const loadViolationRecords = async () => {
  if (userRole.value !== 'student') return
  
  try {
    const res = await violationAPI.getMyViolations()
    violationRecords.value = res
  } catch (error) {
    ElMessage.error('加载违规记录失败')
  }
}

// 修改密码
const changePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    
    await userAPI.changePassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })
    
    ElMessage.success('密码修改成功')
    passwordFormRef.value.resetFields()
  } catch (error) {
    if (error.response?.data?.msg) {
      ElMessage.error(error.response.data.msg)
    } else if (error !== 'cancel') {
      ElMessage.error('密码修改失败')
    }
  }
}

// 工具函数
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

const getViolationText = (type) => {
  const typeMap = {
    absent: '无故缺席',
    late: '迟到',
    early_leave: '早退',
    misconduct: '行为不当',
    other: '其他'
  }
  return typeMap[type] || type
}

const getViolationType = (type) => {
  const typeMap = {
    absent: 'danger',
    late: 'warning',
    early_leave: 'warning',
    misconduct: 'danger',
    other: 'info'
  }
  return typeMap[type] || 'info'
}

onMounted(() => {
  loadUserInfo()
  loadViolationRecords()
})
</script>

<style scoped>
.user-center {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.basic-info {
  margin-bottom: 30px;
}
.basic-info h3 {
  margin-bottom: 15px;
  color: #333;
}
.password-section {
  margin-bottom: 30px;
}
.violation-section {
  margin-bottom: 30px;
}
.teacher-section {
  margin-bottom: 30px;
}
.function-card {
  height: 180px;
  display: flex;
  flex-direction: column;
}
.function-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.function-header i {
  font-size: 18px;
  color: #1e73ff;
}
.function-card p {
  flex: 1;
  color: #666;
  margin-bottom: 15px;
}
</style>