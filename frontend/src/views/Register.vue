<template>
  <div class="register-page">
    <div class="register-card">
      <h2>账号注册</h2>
      <el-form @submit.prevent="register">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" placeholder="密码" type="password" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.student_id" placeholder="学号" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" block>
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="link" @click="$router.push('/')">
        已有账号？返回登录
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
  password: '',
  student_id: '',
  phone: ''
})

const register = async () => {
  try {
    await axios.post('http://127.0.0.1:8000/api/user/register/', form)
    ElMessage.success('注册成功')
    router.push('/')
  } catch (e) {
    ElMessage.error('注册失败')
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fa;
}

.register-card {
  width: 380px;
  padding: 40px 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.register-card h2 {
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