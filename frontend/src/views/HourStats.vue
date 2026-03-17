<template>
  <div class="stats-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的时长统计</span>
        </div>
      </template>

      <!-- 统计概览 -->
      <div class="stats-overview">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="累计志愿时长" :value="totalHours" suffix="小时" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="参与活动数" :value="activityCount" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="平均每次时长" :value="averageHours" :precision="1" suffix="小时" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="本月时长" :value="monthHours" suffix="小时" />
          </el-col>
        </el-row>
      </div>

      <!-- 时长分布 -->
      <div class="stats-chart">
        <el-divider>时长分布</el-divider>
        <div class="chart-container">
          <div class="chart-item">
            <h4>月度时长趋势</h4>
            <div class="chart-placeholder">
              <el-empty description="图表组件待实现" :image-size="100" />
            </div>
          </div>
          <div class="chart-item">
            <h4>活动类型分布</h4>
            <div class="chart-placeholder">
              <el-empty description="图表组件待实现" :image-size="100" />
            </div>
          </div>
        </div>
      </div>

      <!-- 详细记录 -->
      <div class="stats-details">
        <el-divider>详细记录</el-divider>
        <el-table :data="checkinRecords" border style="width: 100%;">
          <el-table-column prop="apply.batch.activity.name" label="活动名称" />
          <el-table-column prop="apply.batch.batch_name" label="批次" />
          <el-table-column label="活动时间">
            <template #default="{ row }">
              {{ formatTime(row.apply.batch.start_time) }} - {{ formatTime(row.apply.batch.end_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="hours" label="获得时长" />
          <el-table-column label="签到时间">
            <template #default="{ row }">
              {{ formatTime(row.checkin_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="checkin_code" label="签到码" />
        </el-table>
      </div>

      <!-- 导出功能 -->
      <div class="export-section">
        <el-divider>数据导出</el-divider>
        <div class="export-options">
          <el-button type="primary" @click="exportToExcel">
            <i class="el-icon-download"></i> 导出Excel
          </el-button>
          <el-button type="success" @click="exportToPDF">
            <i class="el-icon-document"></i> 导出PDF
          </el-button>
          <el-button type="info" @click="printReport">
            <i class="el-icon-printer"></i> 打印报告
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { activityAPI } from '@/api'

const totalHours = ref(0)
const activityCount = ref(0)
const monthHours = ref(0)
const checkinRecords = ref([])

// 计算平均时长
const averageHours = computed(() => {
  return activityCount.value > 0 ? totalHours.value / activityCount.value : 0
})

// 加载统计数据
const loadStats = async () => {
  try {
    // 加载签到记录
    const appliesRes = await activityAPI.getMyApplies()
    
    // 过滤已签到的记录
    const checkinApplies = appliesRes.filter(apply => apply.checkin)
    checkinRecords.value = checkinApplies.map(apply => apply.checkin)
    
    // 计算统计数据
    activityCount.value = checkinApplies.length
    totalHours.value = checkinApplies.reduce((sum, apply) => sum + (apply.checkin?.hours || 0), 0)
    
    // 计算本月时长（简化版）
    const currentMonth = new Date().getMonth()
    monthHours.value = checkinApplies.reduce((sum, apply) => {
      const checkinMonth = new Date(apply.checkin?.checkin_time).getMonth()
      return checkinMonth === currentMonth ? sum + (apply.checkin?.hours || 0) : sum
    }, 0)
    
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

// 导出功能
const exportToExcel = () => {
  ElMessage.info('Excel导出功能待实现')
}

const exportToPDF = () => {
  ElMessage.info('PDF导出功能待实现')
}

const printReport = () => {
  ElMessage.info('打印功能待实现')
}

// 工具函数
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.stats-page {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stats-overview {
  margin-bottom: 30px;
}
.stats-chart {
  margin-bottom: 30px;
}
.chart-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}
.chart-item h4 {
  margin-bottom: 15px;
  color: #333;
  text-align: center;
}
.chart-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #e6e6e6;
  border-radius: 4px;
  background: #f8f9fa;
}
.stats-details {
  margin-bottom: 30px;
}
.export-section {
  text-align: center;
}
.export-options {
  display: flex;
  justify-content: center;
  gap: 15px;
}
</style>