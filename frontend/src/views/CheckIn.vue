<template>
  <div class="checkin-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>签到打卡</span>
        </div>
      </template>

      <!-- 我的报名记录 -->
      <div class="my-applies">
        <h3>我的报名记录</h3>
        <el-table :data="myApplies" border style="width: 100%;">
          <el-table-column prop="batch.activity.name" label="活动名称" />
          <el-table-column prop="batch.batch_name" label="批次" />
          <el-table-column label="活动时间">
            <template #default="{ row }">
              {{ formatTime(row.batch.start_time) }} - {{ formatTime(row.batch.end_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="审核状态">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="签到状态">
            <template #default="{ row }">
              <el-tag v-if="row.checkin" type="success">已签到</el-tag>
              <el-tag v-else type="info">未签到</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="获得时长">
            <template #default="{ row }">
              {{ row.checkin ? row.checkin.hours + '小时' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                :disabled="row.status !== 'approved' || !!row.checkin"
                @click="handleCheckin(row)">
                {{ row.checkin ? '已签到' : '签到' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 扫码签到 -->
      <div class="qr-checkin" v-if="selectedApply">
        <el-divider>扫码签到</el-divider>
        <div class="qr-section">
          <div class="qr-info">
            <h4>活动信息</h4>
            <p>活动名称：{{ selectedApply.batch.activity.name }}</p>
            <p>批次：{{ selectedApply.batch.batch_name }}</p>
            <p>时间：{{ formatTime(selectedApply.batch.start_time) }} - {{ formatTime(selectedApply.batch.end_time) }}</p>
            <p>地点：{{ selectedApply.batch.activity.address }}</p>
          </div>
          <div class="qr-code">
            <div class="code-display">
              <div class="code-text">{{ checkinCode }}</div>
              <p class="code-hint">请向工作人员出示此签到码</p>
            </div>
          </div>
        </div>
        <div class="checkin-actions">
          <el-button type="primary" @click="confirmCheckin">确认签到</el-button>
          <el-button @click="cancelCheckin">取消</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { activityAPI } from '@/api'

const myApplies = ref([])
const selectedApply = ref(null)
const checkinCode = ref('')

// 加载我的报名记录
const loadMyApplies = async () => {
  try {
    const res = await activityAPI.getMyApplies()
    myApplies.value = res
  } catch (error) {
    ElMessage.error('加载报名记录失败')
  }
}

// 处理签到
const handleCheckin = async (apply) => {
  try {
    await ElMessageBox.confirm(
      `确定要签到「${apply.batch.activity.name} - ${apply.batch.batch_name}」吗？`,
      '签到确认',
      { type: 'warning' }
    )
    
    selectedApply.value = apply
    // 生成随机签到码
    checkinCode.value = Math.random().toString(36).substring(2, 8).toUpperCase()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('签到确认失败')
    }
  }
}

// 确认签到
const confirmCheckin = async () => {
  try {
    await activityAPI.checkin(selectedApply.value.batch.activity.id, selectedApply.value.id)
    ElMessage.success('签到成功！')
    selectedApply.value = null
    checkinCode.value = ''
    loadMyApplies()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '签到失败')
  }
}

// 取消签到
const cancelCheckin = () => {
  selectedApply.value = null
  checkinCode.value = ''
}

// 工具函数
const getStatusText = (status) => {
  const statusMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return typeMap[status] || 'info'
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadMyApplies()
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
.my-applies {
  margin-bottom: 30px;
}
.qr-checkin {
  margin-top: 30px;
}
.qr-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 40px;
}
.qr-info {
  flex: 1;
}
.qr-info h4 {
  margin-bottom: 15px;
  color: #333;
}
.qr-info p {
  margin: 8px 0;
  color: #666;
}
.qr-code {
  flex: 0 0 200px;
}
.code-display {
  text-align: center;
  padding: 20px;
  border: 2px solid #e6e6e6;
  border-radius: 8px;
  background: #f8f9fa;
}
.code-text {
  font-size: 24px;
  font-weight: bold;
  color: #1e73ff;
  letter-spacing: 2px;
  margin-bottom: 10px;
}
.code-hint {
  font-size: 12px;
  color: #999;
  margin: 0;
}
.checkin-actions {
  text-align: center;
  margin-top: 20px;
}
</style>