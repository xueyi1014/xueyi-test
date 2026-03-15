<template>
  <div class="activity-page">
    <div class="header">
      <h2>志愿活动列表</h2>
      <el-button @click="$router.push('/home')">
        返回首页
      </el-button>
    </div>
    <div class="list">
      <div class="item" v-for="item in 3" :key="item">
        <h3>社区服务活动</h3>
        <p>时间：2025-01-01</p>
        <el-button type="primary" size="small">
          查看详情
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.activity-page {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.item {
  background: white;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
</style>