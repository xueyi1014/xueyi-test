<template>
  <div class="user-page">
    <div class="card">
      <h2>个人中心</h2>
      <p>用户名：admin</p>
      <p>学号：2025001</p>
      <p>已参加活动：2次</p>
      <el-button @click="logout" type="danger" style="margin-top:10px">
        退出登录
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const logout = () => {
  localStorage.clear()
  router.push('/')
}
</script>

<style scoped>
.user-page {
  padding: 20px;
}
.card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
</style>

