<template>
  <router-view></router-view>
</template>

<script setup>
// 根组件仅挂载路由
</script>

<style>
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
body {
  font-family: "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px;
  color: #333;
}
</style>