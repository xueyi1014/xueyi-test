<template>
  <div class="home">
    <div class="header">
      <h1>首页</h1>
      <div class="nav">
        <el-button link @click="$router.push('/activity')">
          志愿活动
        </el-button>
        <el-button link @click="$router.push('/user')">
          个人中心
        </el-button>
      </div>
    </div>
    <div class="content">
      <div class="card">欢迎使用志愿服务平台</div>
    </div>
  </div>
</template>

<style scoped>
.home {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
</style>