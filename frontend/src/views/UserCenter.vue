<template>
  <div class="user-page">
    <div class="profile-card">
      <div class="avatar">
        <span class="avatar-text">{{ username.charAt(0) }}</span>
      </div>
      <div class="info">
        <h3>{{ username }}</h3>
        <p>学号：{{ studentId }}</p>
        <p>手机号：{{ phone }}</p>
      </div>
    </div>

    <div class="activity-card">
      <div class="card-header">
        <h4>我参与的志愿活动</h4>
      </div>
      <div class="empty">暂无参与活动</div>
    </div>

    <div class="logout-box">
      <el-button type="danger" block @click="logout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
const router = useRouter()

const username = ref('')
const studentId = ref('')
const phone = ref('')

// 获取真实用户信息
onMounted(async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/user/info/')
    username.value = res.data.username
    studentId.value = res.data.student_id
    phone.value = res.data.phone
  } catch (e) {
    ElMessage.error('登录已过期')
    router.push('/')
  }
})

// 退出登录
const logout = () => {
  localStorage.clear()
  ElMessage.success('退出成功')
  router.push('/')
}
</script>

<style scoped>
.user-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}
.profile-card {
  background: #fff;
  border-radius: 14px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}
.avatar {
  width: 60px;
  height: 60px;
  background: #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-text {
  font-size: 22px;
  color: #fff;
  font-weight: 500;
}
.info h3 {
  margin: 0 0 6px 0;
  font-size: 18px;
  font-weight: 500;
}
.info p {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}
.activity-card {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}
.card-header {
  margin-bottom: 16px;
}
.card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}
.empty {
  color: #999;
  padding: 20px 0;
  text-align: center;
}
.logout-box {
  margin-top: 10px;
}
</style>