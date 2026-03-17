<template>
  <div class="checkin-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>签到打卡</span>
        </div>
      </template>

      <!-- 标签页 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 可签到活动 -->
        <el-tab-pane label="可签到活动" name="available">
          <div v-loading="loading">
            <el-table :data="availableActivities" stripe style="width: 100%">
              <el-table-column prop="activity_name" label="活动名称" min-width="200" />
              <el-table-column prop="batch_name" label="批次" width="150" />
              <el-table-column label="活动时间" width="280">
                <template #default="{ row }">
                  {{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="address" label="活动地点" width="150" />
              <el-table-column label="签到状态" width="120">
                <template #default="{ row }">
                  <el-tag v-if="row.check_in_time" type="success">已签到</el-tag>
                  <el-tag v-else-if="row.check_out_time" type="info">已签退</el-tag>
                  <el-tag v-else type="warning">未签到</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button 
                    v-if="!row.check_in_time && canCheckIn(row)"
                    type="primary" 
                    size="small"
                    @click="handleCheckIn(row)">
                    签到
                  </el-button>
                  <el-button 
                    v-if="row.check_in_time && !row.check_out_time"
                    type="success" 
                    size="small"
                    @click="handleCheckOut(row)">
                    签退
                  </el-button>
                  <el-tag v-if="row.check_out_time" type="info" size="small">已完成</el-tag>
                  <el-tag v-if="!row.check_in_time && !canCheckIn(row)" type="info" size="small">未到签到时间</el-tag>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="!loading && availableActivities.length === 0" class="empty-state">
              <el-empty description="暂无可签到活动" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 历史签到记录 -->
        <el-tab-pane label="历史签到记录" name="history">
          <div v-loading="loading">
            <el-table :data="historyRecords" stripe style="width: 100%">
              <el-table-column prop="activity_name" label="活动名称" min-width="200" />
              <el-table-column prop="batch_name" label="批次" width="150" />
              <el-table-column label="签到时间" width="180">
                <template #default="{ row }">
                  {{ row.check_in_time ? formatTime(row.check_in_time) : '-' }}
                </template>
              </el-table-column>
              <el-table-column label="签退时间" width="180">
                <template #default="{ row }">
                  {{ row.check_out_time ? formatTime(row.check_out_time) : '-' }}
                </template>
              </el-table-column>
              <el-table-column label="时长（小时）" width="120">
                <template #default="{ row }">
                  {{ row.hours || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag v-if="row.check_out_time" type="success">已完成</el-tag>
                  <el-tag v-else-if="row.check_in_time" type="warning">进行中</el-tag>
                  <el-tag v-else type="info">未开始</el-tag>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="!loading && historyRecords.length === 0" class="empty-state">
              <el-empty description="暂无签到记录" />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { activityAPI } from '@/api'

const activeTab = ref('available')
const myApplies = ref([])
const loading = ref(false)

// 可签到活动 - 已审核通过且在活动时间范围内
const availableActivities = computed(() => {
  return myApplies.value.filter(apply => 
    apply.status === 'approved' && 
    apply.batch &&
    apply.batch.activity
  ).map(apply => ({
    apply_id: apply.id, // 报名 ID
    activity_id: apply.batch.activity.id, // 活动 ID
    activity_name: apply.batch.activity.name,
    batch_name: apply.batch.batch_name,
    start_time: apply.batch.start_time,
    end_time: apply.batch.end_time,
    address: apply.batch.activity.address,
    check_in_time: apply.check_in_time,
    check_out_time: apply.check_out_time,
    hours: apply.hours
  }))
})

// 历史签到记录 - 所有有签到记录的活动
const historyRecords = computed(() => {
  return myApplies.value.filter(apply => 
    apply.check_in_time || apply.check_out_time
  ).map(apply => ({
    apply_id: apply.id,
    activity_id: apply.batch?.activity?.id || null,
    activity_name: apply.batch?.activity?.name || '未知活动',
    batch_name: apply.batch?.batch_name || '未知批次',
    check_in_time: apply.check_in_time,
    check_out_time: apply.check_out_time,
    hours: apply.hours
  }))
})

// 判断是否可以签到（在活动开始时间前30分钟到活动结束时间内）
const canCheckIn = (activity) => {
  const now = new Date()
  const startTime = new Date(activity.start_time)
  const endTime = new Date(activity.end_time)
  const checkInTime = new Date(startTime.getTime() - 30 * 60 * 1000) // 提前30分钟
  
  return now >= checkInTime && now <= endTime
}

// 加载我的报名记录
const loadMyApplies = async () => {
  try {
    loading.value = true
    const res = await activityAPI.getMyApplies()
    myApplies.value = res
  } catch (error) {
    ElMessage.error('加载报名记录失败')
  } finally {
    loading.value = false
  }
}

// 处理签到
const handleCheckIn = async (record) => {
  try {
    await activityAPI.checkin(record.activity_id, record.apply_id)
    ElMessage.success('签到成功！')
    await loadMyApplies()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '签到失败')
  }
}

// 处理签退
const handleCheckOut = async (record) => {
  try {
    await activityAPI.checkout(record.activity_id, record.apply_id)
    ElMessage.success('签退成功！')
    await loadMyApplies()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '签退失败')
  }
}

// 标签切换
const handleTabChange = (tab) => {
  console.log('切换到标签:', tab)
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  const userRole = localStorage.getItem('userRole')
  if (userRole === 'student') {
    loadMyApplies()
  }
})
</script>

<style scoped>
.checkin-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  margin-top: 40px;
  text-align: center;
}
</style>