<template>
  <div class="login-wrapper">
    <div class="login-container">
      <!-- 左侧标题区域 -->
      <div class="left-box">
        <div class="title-group">
          <h1>校园志愿服务平台</h1>
          <p>Campus Volunteer Service Platform</p>
        </div>
      </div>

      <!-- 右侧登录卡片 -->
      <div class="right-box">
        <div class="login-card">
          <h2>用户登录</h2>

          <el-form @submit.prevent="login">
            <!-- 用户名 -->
            <el-form-item>
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                prefix-icon="el-icon-user"
              />
            </el-form-item>

            <!-- 密码 -->
            <el-form-item>
              <el-input
                v-model="form.password"
                :type="isShowPwd ? 'text' : 'password'"
                placeholder="请输入密码"
                prefix-icon="el-icon-lock"
                suffix-icon="el-icon-view"
                @clickSuffix="isShowPwd = !isShowPwd"
              />
            </el-form-item>

            <!-- 登录按钮 -->
            <el-form-item>
              <el-button type="primary" native-type="submit" block>
                登录
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 注册链接 -->
          <div class="register-link" @click="$router.push('/register')">
            没有账号？立即注册
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
const router = useRouter()

const form = reactive({ username: '', password: '' })
const isShowPwd = ref(false)

const login = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  try {
    const res = await axios.post('/api/user/token/', form)
    localStorage.token = res.data.access
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (e) {
    ElMessage.error('账号或密码错误，请重新输入')
  }
}
</script>

<style scoped>
/* 外层背景 */
.login-wrapper {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #1e73ff 0%, #0050e6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 中间容器 */
.login-container {
  width: 900px;
  height: 500px;
  background: #ffffff15;
  border-radius: 20px;
  display: flex;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

/* 左侧 */
.left-box {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.title-group h1 {
  font-size: 36px;
  color: #fff;
  margin: 0 0 10px 0;
  font-weight: 500;
}

.title-group p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

/* 右侧 */
.right-box {
  width: 400px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 320px;
}

.login-card h2 {
  text-align: center;
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 30px;
  color: #333;
}

/* 注册链接 */
.register-link {
  text-align: center;
  color: #1e73ff;
  font-size: 14px;
  cursor: pointer;
  margin-top: 20px;
}
</style>