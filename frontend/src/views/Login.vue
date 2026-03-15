<template>
  <div class="login-page">
    <div class="login-card">
      <h2>校园志愿服务平台</h2>
      <el-form @submit.prevent="login">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" placeholder="密码" type="password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" block>
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="link" @click="$router.push('/register')">
        没有账号？前往注册
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
const router = useRouter()

const form = reactive({
  username: '',
  password: ''
})

const login = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/user/token/', form)
    localStorage.token = res.data.access
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (e) {
    ElMessage.error('登录失败')
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fa;
}

.login-card {
  width: 380px;
  padding: 40px 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.login-card h2 {
  text-align: center;
  margin-bottom: 30px;
  font-weight: 500;
}

.link {
  text-align: center;
  color: #409eff;
  cursor: pointer;
  margin-top: 10px;
}
</style>