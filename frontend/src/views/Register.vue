<template>
  <div class="login-wrapper">
    <div class="login-container">
      <div class="left-box">
        <div class="title-group">
          <h1>校园志愿服务平台</h1>
          <p>Campus Volunteer Service Platform</p>
        </div>
      </div>

      <div class="right-box">
        <div class="login-card">
          <h2>账号注册</h2>

          <!-- 表单提交绑定 -->
          <el-form @submit.prevent="register" label-width="80px">
            <!-- 身份选择 -->
            <el-form-item label="身份">
              <el-radio-group v-model="form.role">
                <el-radio label="student">学生</el-radio>
                <el-radio label="teacher">老师</el-radio>
              </el-radio-group>
            </el-form-item>

            <!-- 用户名 -->
            <el-form-item label="用户名">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                prefix-icon="el-icon-user"
              />
            </el-form-item>

            <!-- 密码 -->
            <el-form-item label="密码">
              <el-input
                v-model="form.password"
                :type="isShowPwd ? 'text' : 'password'"
                placeholder="请输入密码（至少6位）"
                prefix-icon="el-icon-lock"
                suffix-icon="el-icon-view"
                @clickSuffix="isShowPwd = !isShowPwd"
              />
            </el-form-item>

            <!-- 学号/工号 -->
            <el-form-item :label="form.role === 'student' ? '学号' : '工号'">
              <el-input
                v-model="form.idNumber"
                :placeholder="form.role === 'student' ? '请输入学号' : '请输入工号'"
                prefix-icon="el-icon-school"
              />
            </el-form-item>

            <!-- 手机号 -->
            <el-form-item label="手机号">
              <el-input
                v-model="form.phone"
                placeholder="请输入手机号"
                prefix-icon="el-icon-phone"
              />
            </el-form-item>

            <!-- 注册按钮 -->
            <el-form-item>
              <el-button type="primary" native-type="submit" block>注册</el-button>
            </el-form-item>
          </el-form>

          <!-- 跳转登录 -->
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
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
// 导入封装的request工具
import request from '@/utils/request'

const router = useRouter()

// 表单数据
const form = reactive({
  role: '',        // student/teacher
  username: '',    // 用户名
  password: '',    // 密码
  idNumber: '',    // 学号/工号
  phone: ''        // 手机号
})

// 显示密码开关
const isShowPwd = ref(false)

// 注册方法（简化验证，确保能请求）
const register = async () => {
  // 基础验证
  if (!form.role) {
    ElMessage.warning('请选择身份！')
    return
  }
  if (!form.username || form.username.length < 2) {
    ElMessage.warning('用户名至少2位！')
    return
  }
  if (!form.password || form.password.length < 6) {
    ElMessage.warning('密码至少6位！')
    return
  }
  if (!form.idNumber) {
    ElMessage.warning(`请输入${form.role === 'student' ? '学号' : '工号'}！`)
    return
  }
  if (!/^1\d{10}$/.test(form.phone)) {
    ElMessage.warning('请输入正确的手机号（11位）！')
    return
  }

  try {
    // 发送注册请求（兼容带/路径）
    const res = await request.post('/api/user/register/', form)
    ElMessage.success('注册成功！即将跳转到登录页')
    // 延迟跳转
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } catch (err) {
    // 错误提示
    const errorMsg = err.response?.data?.msg || '注册失败，请稍后重试'
    ElMessage.error(errorMsg)
  }
}
</script>

<style scoped>
.login-wrapper {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #1e73ff 0%, #0050e6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-container {
  width: 900px;
  height: 550px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  display: flex;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}
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
.register-link {
  text-align: center;
  color: #1e73ff;
  font-size: 14px;
  cursor: pointer;
  margin-top: 20px;
}
</style>