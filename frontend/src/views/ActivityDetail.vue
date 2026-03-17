<template>
  <div class="detail-page">
    <el-card v-if="activity" class="activity-card">
      <!-- 活动头部 -->
      <div class="activity-header">
        <div class="header-left">
          <h1>{{ activity.name }}</h1>
          <div class="activity-meta">
            <el-tag :type="getStatusType(activity.status)">{{ getStatusText(activity.status) }}</el-tag>
            <el-tag :type="getTypeType(activity.type)">{{ getTypeText(activity.type) }}</el-tag>
            <span class="organizer">主办方：{{ activity.organizer }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-button 
            :type="isFavorite ? 'warning' : 'default'" 
            :icon="isFavorite ? 'el-icon-star-on' : 'el-icon-star-off'"
            @click="toggleFavorite">
            {{ isFavorite ? '已收藏' : '收藏' }}
          </el-button>
        </div>
      </div>

      <!-- 活动基本信息 -->
      <div class="activity-info">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="info-item">
              <i class="el-icon-location"></i>
              <span>活动地点：{{ activity.address }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="info-item">
              <i class="el-icon-user"></i>
              <span>总名额：{{ activity.total_quota }}人</span>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 活动批次 -->
      <div class="batches-section">
        <h3>活动批次</h3>
        <div class="batch-list">
          <div v-for="batch in activity.batches" :key="batch.id" class="batch-card">
            <div class="batch-info">
              <h4>{{ batch.batch_name }}</h4>
              <p>时间：{{ formatTime(batch.start_time) }} - {{ formatTime(batch.end_time) }}</p>
              <p>名额：{{ batch.quota }}人（已报名：{{ batch.apply_count }}人）</p>
              <p>剩余：{{ batch.quota - batch.apply_count }}人</p>
            </div>
            <div class="batch-actions">
              <el-button 
                type="primary" 
                :disabled="batch.quota <= batch.apply_count || activity.status !== 'published'"
                @click="applyForBatch(batch.id)">
                报名此批次
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 活动详情 -->
      <div class="activity-details">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="工作内容" name="description">
            <div class="detail-content">
              <h4>工作内容</h4>
              <p>{{ activity.description || '暂无描述' }}</p>
            </div>
          </el-tab-pane>
          <el-tab-pane label="培训说明" name="training">
            <div class="detail-content">
              <h4>培训说明</h4>
              <p>{{ activity.training || '暂无培训说明' }}</p>
            </div>
          </el-tab-pane>
          <el-tab-pane label="活动保障" name="support">
            <div class="detail-content">
              <h4>活动保障</h4>
              <p>{{ activity.support || '暂无保障说明' }}</p>
            </div>
          </el-tab-pane>
          <el-tab-pane label="注意事项" name="notice">
            <div class="detail-content">
              <h4>注意事项</h4>
              <p>{{ activity.notice || '暂无注意事项' }}</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>

    <!-- 冲突检测对话框 -->
    <el-dialog v-model="showConflictDialog" title="时间冲突检测" width="500px">
      <div v-if="conflicts.length > 0">
        <el-alert title="检测到时间冲突" type="error" show-icon>
          <p>以下事项与您选择的活动时间冲突：</p>
        </el-alert>
        <div class="conflict-list">
          <div v-for="conflict in conflicts" :key="conflict.message" class="conflict-item">
            <p>{{ conflict.message }}</p>
            <p class="conflict-time">{{ formatTime(conflict.start_time) }} - {{ formatTime(conflict.end_time) }}</p>
          </div>
        </div>
        <p style="margin-top: 15px; color: #f56c6c;">请解决冲突后再进行报名</p>
      </div>
      <div v-else>
        <el-alert title="无时间冲突" type="success" show-icon>
          <p>您可以选择此批次进行报名</p>
        </el-alert>
      </div>
      <template #footer>
        <el-button @click="showConflictDialog = false">关闭</el-button>
        <el-button v-if="conflicts.length === 0" type="primary" @click="confirmApply">确认报名</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { activityAPI, favoriteAPI, conflictAPI } from '@/api'

const route = useRoute()
const activity = ref(null)
const isFavorite = ref(false)
const activeTab = ref('description')
const showConflictDialog = ref(false)
const conflicts = ref([])
const selectedBatchId = ref(null)

// 加载活动详情
const loadActivityDetail = async () => {
  try {
    const res = await activityAPI.getDetail(route.params.id)
    activity.value = res
    
    // 检查是否已收藏
    await checkFavoriteStatus()
  } catch (error) {
    ElMessage.error('加载活动详情失败')
  }
}

// 检查收藏状态
const checkFavoriteStatus = async () => {
  try {
    const res = await favoriteAPI.isFavorite(route.params.id)
    isFavorite.value = res.is_favorite
  } catch (error) {
    console.error('检查收藏状态失败:', error)
  }
}

// 切换收藏
const toggleFavorite = async () => {
  try {
    if (isFavorite.value) {
      await favoriteAPI.unfavorite(route.params.id)
      ElMessage.success('取消收藏成功')
      isFavorite.value = false
    } else {
      await favoriteAPI.favorite(route.params.id)
      ElMessage.success('收藏成功')
      isFavorite.value = true
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 报名批次
const applyForBatch = async (batchId) => {
  selectedBatchId.value = batchId
  
  // 检查时间冲突
  try {
    const res = await conflictAPI.checkConflict(route.params.id, batchId)
    conflicts.value = res.conflicts
    showConflictDialog.value = true
  } catch (error) {
    ElMessage.error('冲突检测失败')
  }
}

// 确认报名
const confirmApply = async () => {
  try {
    await activityAPI.apply({
      activity_id: route.params.id,
      batch_id: selectedBatchId.value
    })
    
    ElMessage.success('报名成功，等待审核')
    showConflictDialog.value = false
    
    // 重新加载活动详情以更新报名人数
    loadActivityDetail()
  } catch (error) {
    ElMessage.error('报名失败')
  }
}

// 工具函数
const getStatusText = (status) => {
  const statusMap = {
    draft: '草稿',
    published: '已发布',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    published: 'success',
    cancelled: 'danger'
  }
  return typeMap[status] || 'info'
}

const getTypeText = (type) => {
  const typeMap = {
    campus: '校园服务',
    community: '社区服务',
    environment: '环保活动',
    other: '其他'
  }
  return typeMap[type] || type
}

const getTypeType = (type) => {
  const typeMap = {
    campus: 'primary',
    community: 'success',
    environment: 'warning',
    other: 'info'
  }
  return typeMap[type] || 'info'
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadActivityDetail()
})
</script>

<style scoped>
.detail-page {
  padding: 20px;
}
.activity-card {
  max-width: 1200px;
  margin: 0 auto;
}
.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.header-left h1 {
  margin: 0 0 10px 0;
  color: #333;
}
.activity-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}
.organizer {
  color: #666;
  font-size: 14px;
}
.activity-info {
  margin: 20px 0;
}
.info-item {
  display: flex;
  align-items: center;
  margin: 10px 0;
}
.info-item i {
  margin-right: 8px;
  color: #409eff;
}
.batches-section {
  margin: 30px 0;
}
.batch-list {
  display: grid;
  gap: 15px;
}
.batch-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  background: #f9f9f9;
}
.batch-info h4 {
  margin: 0 0 8px 0;
  color: #333;
}
.batch-info p {
  margin: 4px 0;
  color: #666;
}
.activity-details {
  margin-top: 30px;
}
.detail-content {
  padding: 15px 0;
}
.detail-content h4 {
  margin-bottom: 10px;
  color: #333;
}
.conflict-list {
  margin-top: 15px;
}
.conflict-item {
  padding: 10px;
  border: 1px solid #f56c6c;
  border-radius: 4px;
  margin-bottom: 10px;
  background: #fef0f0;
}
.conflict-time {
  color: #f56c6c;
  font-size: 12px;
}
</style>