<template>
  <div class="hour-stats-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>我的时长统计</span>
        </div>
      </template>

      <!-- 统计概览 -->
      <div class="stats-overview">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ stats.total_hours || 0 }}</div>
                <div class="stat-label">累计时长（小时）</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ stats.completed_activities || 0 }}</div>
                <div class="stat-label">已参与活动数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ stats.month_hours || 0 }}</div>
                <div class="stat-label">本月时长（小时）</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ stats.pending_hours || 0 }}</div>
                <div class="stat-label">待审核时长</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 图表展示 -->
      <div class="charts-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>近6个月时长趋势</span>
              </template>
              <div ref="trendChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>活动类型占比</span>
              </template>
              <div ref="pieChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 筛选和表格 -->
      <div class="details-section">
        <el-divider>时长明细</el-divider>
        <div class="filter-bar">
          <el-select v-model="monthFilter" placeholder="按月份筛选" clearable style="width: 150px;" @change="filterDetails">
            <el-option label="全部" value="" />
            <el-option v-for="month in availableMonths" :key="month" :label="month" :value="month" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="按状态筛选" clearable style="width: 150px;" @change="filterDetails">
            <el-option label="全部" value="" />
            <el-option label="已完成" value="completed" />
            <el-option label="待审核" value="pending" />
          </el-select>
        </div>
        <el-table :data="filteredDetails" stripe style="width: 100%; margin-top: 20px;" v-if="filteredDetails.length > 0">
          <el-table-column prop="activity_name" label="活动名称" min-width="200" />
          <el-table-column prop="activity_type" label="活动类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getTypeColor(row.activity_type)">{{ getTypeText(row.activity_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="活动时间" width="280">
            <template #default="{ row }">
              {{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="hours" label="时长（小时）" width="120" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'warning'">
                {{ row.status === 'completed' ? '已完成' : '待审核' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无时长记录" style="margin-top: 40px;" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { userAPI } from '@/api'

const loading = ref(false)
const stats = ref({
  total_hours: 0,
  completed_activities: 0,
  month_hours: 0,
  pending_hours: 0,
  monthly_stats: [],
  type_stats: [],
  details: []
})

const monthFilter = ref('')
const statusFilter = ref('')
const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null

const availableMonths = computed(() => {
  const months = new Set()
  stats.value.details.forEach(detail => {
    const date = new Date(detail.start_time)
    const monthStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    months.add(monthStr)
  })
  return Array.from(months).sort().reverse()
})

const filteredDetails = computed(() => {
  let details = [...stats.value.details]
  
  if (monthFilter.value) {
    details = details.filter(detail => {
      const date = new Date(detail.start_time)
      const monthStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      return monthStr === monthFilter.value
    })
  }
  
  if (statusFilter.value) {
    details = details.filter(detail => detail.status === statusFilter.value)
  }
  
  return details
})

const loadStats = async () => {
  try {
    loading.value = true
    const res = await userAPI.getHourStats()
    stats.value = res
    
    await nextTick()
    initCharts()
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const initCharts = () => {
  if (trendChartRef.value && pieChartRef.value) {
    setTimeout(() => {
      initTrendChart()
      initPieChart()
    }, 100)
  }
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  
  const container = trendChartRef.value
  if (!container || container.clientWidth === 0 || container.clientHeight === 0) {
    return
  }
  
  trendChart = echarts.init(container)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: stats.value.monthly_stats.map(item => item.month),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '时长（小时）'
    },
    series: [{
      data: stats.value.monthly_stats.map(item => item.hours),
      type: 'line',
      smooth: true,
      areaStyle: {
        color: 'rgba(64, 158, 255, 0.2)'
      },
      lineStyle: {
        color: '#409EFF'
      },
      itemStyle: {
        color: '#409EFF'
      }
    }]
  }
  
  trendChart.setOption(option)
}

const initPieChart = () => {
  if (!pieChartRef.value) return
  
  const container = pieChartRef.value
  if (!container || container.clientWidth === 0 || container.clientHeight === 0) {
    return
  }
  
  pieChart = echarts.init(container)
  
  const typeMap = {
    'campus': '校园服务',
    'community': '社区服务',
    'environment': '环保活动',
    'education': '教育支教',
    'culture': '文化活动',
    'other': '其他活动'
  }
  
  const data = stats.value.type_stats.map(item => ({
    name: typeMap[item.type] || item.type,
    value: item.hours
  }))
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 小时 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      name: '活动类型',
      type: 'pie',
      radius: '50%',
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  pieChart.setOption(option)
}

const getTypeColor = (type) => {
  const colorMap = {
    'campus': 'primary',
    'community': 'success',
    'environment': 'warning',
    'education': 'danger',
    'culture': 'info',
    'other': ''
  }
  return colorMap[type] || ''
}

const getTypeText = (type) => {
  const textMap = {
    'campus': '校园服务',
    'community': '社区服务',
    'environment': '环保活动',
    'education': '教育支教',
    'culture': '文化活动',
    'other': '其他活动'
  }
  return textMap[type] || type
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const filterDetails = () => {
}

const handleResize = () => {
  if (trendChart) trendChart.resize()
  if (pieChart) pieChart.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
  if (pieChart) {
    pieChart.dispose()
    pieChart = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.hour-stats-page {
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

.stat-card {
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.stat-content {
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.charts-section {
  margin-bottom: 30px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.details-section {
  margin-top: 30px;
}

.filter-bar {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
