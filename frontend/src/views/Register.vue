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

      <!-- 右侧注册卡片 -->
      <div class="right-box">
        <div class="login-card">
          <h2>账号注册</h2>

          <el-form @submit.prevent="register">
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

            <!-- 学号 -->
            <el-form-item>
              <el-input
                v-model="form.student_id"
                placeholder="请输入学号"
                prefix-icon="el-icon-school"
              />
            </el-form-item>

            <!-- 手机号 -->
            <el-form-item>
              <el-input
                v-model="form.phone"
                placeholder="请输入手机号"
                prefix-icon="el-icon-phone"
              />
            </el-form-item>

            <!-- 注册按钮 -->
            <el-form-item>
              <el-button type="primary" native-type="submit" block>
                注册
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 登录链接 -->
          <div class="register-link" @click="$router.push('/')">
            已有账号？返回登录
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

const form = reactive({
  username: '',
  password: '',
  student_id: '',
  phone: ''
})
const isShowPwd = ref(false)

const register = async () => {
  if (!form.username || form.username.length < 4) {
    ElMessage.warning('用户名至少4位')
    return
  }
  const pwdReg = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,16}$/
  if (!pwdReg.test(form.password)) {
    ElMessage.warning('密码必须8-16位，包含大写、小写、数字、符号!@#$%^&*')
    return
  }
  const stuReg = /^20224630\d{5}$/
  if (!stuReg.test(form.student_id)) {
    ElMessage.warning('学号必须是13位，格式：20224630开头')
    return
  }
  const phoneReg = /^1\d{10}$/
  if (!phoneReg.test(form.phone)) {
    ElMessage.warning('请输入正确的11位手机号')
    return
  }

  try {
    await axios.post('/api/user/register/', form)
    ElMessage.success('注册成功')
    router.push('/')
  } catch (err) {
    const msg = err.response?.data?.msg || '注册失败'
    ElMessage.error(msg)
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

/* 登录链接 */
.register-link {
  text-align: center;
  color: #1e73ff;
  font-size: 14px;
  cursor: pointer;
  margin-top: 20px;
}
</style>