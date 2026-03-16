<template>
  <!-- 只保留路由视图挂载点，无任何多余内容 -->
  <router-view></router-view>
</template>

<script setup>
// 根组件无需任何业务逻辑，仅做路由挂载
</script>

<style>
/* 全局样式重置，保证页面兼容性 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 全局字体设置，贴近真实政务系统风格 */
body {
  font-family: "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px;
  color: #333;
}
</style>