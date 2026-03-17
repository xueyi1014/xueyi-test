<template>
  <div class="activity-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>志愿活动列表</span>
          <el-button v-if="userRole === 'teacher'" type="primary" @click="showCreateDialog = true">发布新活动</el-button>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <div class="filter-bar">
        <el-input v-model="searchKeyword" placeholder="搜索活动名称" style="width: 200px;" clearable />
        <el-select v-model="filterType" placeholder="活动类型" clearable style="margin-left: 10px; width: 150px;">
          <el-option label="校园服务" value="campus" />
          <el-option label="社区服务" value="community" />
          <el-option label="环保活动" value="environment" />
          <el-option label="其他" value="other" />
        </el-select>
        <el-select v-model="filterLocation" placeholder="活动地点" clearable style="margin-left: 10px; width: 150px;">
          <el-option label="校内" value="campus" />
          <el-option label="校外" value="off-campus" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="活动状态" clearable style="margin-left: 10px; width: 150px;">
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="进行中" value="ongoing" />
          <el-option label="已结束" value="ended" />
        </el-select>
        <el-select v-model="filterDuration" placeholder="时长范围" clearable style="margin-left: 10px; width: 150px;">
          <el-option label="1小时以内" value="0-1" />
          <el-option label="1-3小时" value="1-3" />
          <el-option label="3小时以上" value="3+" />
        </el-select>
        <el-date-picker
          v-model="filterTimeRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="margin-left: 10px; width: 280px;"
        />
      </div>

      <!-- 活动表格 -->
      <el-table :data="filteredActivities" style="width: 100%; margin-top: 20px;" v-loading="loading" stripe>
        <el-table-column prop="name" label="活动名称" min-width="200" />
        <el-table-column prop="type" label="活动类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">{{ getTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="活动地点" width="150" />
        <el-table-column label="活动时间" width="300">
          <template #default="{ row }">
            <div v-if="row.batches && row.batches.length > 0">
              <div v-for="batch in row.batches.slice(0, 2)" :key="batch.id" class="batch-time">
                {{ formatTime(batch.start_time) }} - {{ formatTime(batch.end_time) }}
              </div>
              <div v-if="row.batches.length > 2" class="more-batches">
                还有 {{ row.batches.length - 2 }} 个批次
              </div>
            </div>
            <span v-else>暂无批次</span>
          </template>
        </el-table-column>
        <el-table-column label="招募名额" width="120">
          <template #default="{ row }">
            <div class="quota-info">
              <span>{{ row.total_apply_count || 0 }}/{{ row.total_quota || 0 }}</span>
              <el-progress 
                :percentage="getQuotaPercentage(row)" 
                :color="getQuotaColor(row)"
                :show-text="false"
                style="margin-top: 4px;"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="userRole === 'student'" type="primary" size="small" @click="showApplyDialog(row)">
              报名
            </el-button>
            <el-button type="info" size="small" @click="viewDetail(row)">
              查看详情
            </el-button>
            <template v-if="userRole === 'teacher'">
              <el-button type="warning" size="small" @click="editActivity(row)">编辑</el-button>
              <el-button type="danger" size="small" @click="deleteActivity(row.id)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-if="!loading && filteredActivities.length === 0" class="empty-state">
        <el-empty description="暂无活动数据" />
      </div>
    </el-card>

    <!-- 报名对话框 -->
    <el-dialog v-model="showApplyDialogVisible" title="选择活动批次" width="600px">
      <el-table :data="selectedActivity?.batches || []" style="width: 100%">
        <el-table-column prop="batch_name" label="批次名称" />
        <el-table-column label="时间段">
          <template #default="{ row }">
            {{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="名额">
          <template #default="{ row }">
            {{ row.apply_count }}/{{ row.quota }}
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small"
              :disabled="row.apply_count >= row.quota"
              @click="confirmApply(row.id)">
              {{ row.apply_count >= row.quota ? '已满' : '报名' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 活动详情对话框 -->
    <el-dialog v-model="showDetailDialogVisible" title="活动详情" width="800px">
      <el-descriptions :column="2" border v-if="selectedActivity">
        <el-descriptions-item label="活动名称">{{ selectedActivity.name }}</el-descriptions-item>
        <el-descriptions-item label="活动类型">{{ getTypeText(selectedActivity.type) }}</el-descriptions-item>
        <el-descriptions-item label="主办方">{{ selectedActivity.organizer }}</el-descriptions-item>
        <el-descriptions-item label="活动地点">{{ selectedActivity.address }}</el-descriptions-item>
        <el-descriptions-item label="总名额">{{ selectedActivity.total_quota || 0 }}</el-descriptions-item>
        <el-descriptions-item label="已报名">{{ selectedActivity.total_apply_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedActivity.status)">{{ getStatusText(selectedActivity.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="工作内容" :span="2">{{ selectedActivity.description || '暂无描述' }}</el-descriptions-item>
        <el-descriptions-item label="培训说明" :span="2">{{ selectedActivity.training || '无' }}</el-descriptions-item>
        <el-descriptions-item label="活动保障" :span="2">{{ selectedActivity.support || '无' }}</el-descriptions-item>
        <el-descriptions-item label="注意事项" :span="2">{{ selectedActivity.notice || '无' }}</el-descriptions-item>
      </el-descriptions>
      <el-divider>活动批次</el-divider>
      <el-table :data="selectedActivity?.batches || []" stripe>
        <el-table-column prop="batch_name" label="批次名称" />
        <el-table-column label="时间段">
          <template #default="{ row }">{{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}</template>
        </el-table-column>
        <el-table-column label="名额">
          <template #default="{ row }">{{ row.apply_count }}/{{ row.quota }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showDetailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 发布活动对话框 -->
    <el-dialog v-model="showCreateDialog" title="发布新活动" width="600px">
      <el-form :model="newActivity" label-width="100px">
        <el-form-item label="活动名称">
          <el-input v-model="newActivity.name" placeholder="请输入活动名称" />
        </el-form-item>
        <el-form-item label="活动类型">
          <el-select v-model="newActivity.type" placeholder="请选择活动类型">
            <el-option label="校园服务" value="campus" />
            <el-option label="社区服务" value="community" />
            <el-option label="环保活动" value="environment" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="主办方">
          <el-input v-model="newActivity.organizer" placeholder="请输入主办方" />
        </el-form-item>
        <el-form-item label="活动地点">
          <el-input v-model="newActivity.address" placeholder="请输入活动地点" />
        </el-form-item>
        <el-form-item label="活动描述">
          <el-input v-model="newActivity.description" type="textarea" :rows="3" placeholder="请输入活动描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createActivity">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { activityAPI } from '@/api'

const router = useRouter()
const userRole = ref(localStorage.getItem('userRole') || 'student')
const activities = ref([])
const searchKeyword = ref('')
const filterType = ref('')
const filterLocation = ref('')
const filterStatus = ref('')
const filterDuration = ref('')
const filterTimeRange = ref([])
const showCreateDialog = ref(false)
const showApplyDialogVisible = ref(false)
const showDetailDialogVisible = ref(false)
const selectedActivity = ref(null)
const loading = ref(false)

const newActivity = ref({
  name: '',
  type: '',
  organizer: '',
  address: '',
  description: ''
})

// 过滤活动列表
const filteredActivities = computed(() => {
  return activities.value.filter(activity => {
    const matchesKeyword = !searchKeyword.value || activity.name.includes(searchKeyword.value)
    const matchesType = !filterType.value || activity.type === filterType.value
    const matchesLocation = !filterLocation.value || 
      (filterLocation.value === 'campus' && activity.address.includes('校')) ||
      (filterLocation.value === 'off-campus' && !activity.address.includes('校'))
    const matchesStatus = !filterStatus.value || activity.status === filterStatus.value
    const matchesTimeRange = !filterTimeRange.value || filterTimeRange.value.length === 0 ||
      (new Date(activity.create_time) >= new Date(filterTimeRange.value[0]) &&
       new Date(activity.create_time) <= new Date(filterTimeRange.value[1]))
    
    let matchesDuration = true
    if (filterDuration.value) {
      const duration = calculateDuration(activity)
      if (filterDuration.value === '0-1') {
        matchesDuration = duration <= 1
      } else if (filterDuration.value === '1-3') {
        matchesDuration = duration > 1 && duration <= 3
      } else if (filterDuration.value === '3+') {
        matchesDuration = duration > 3
      }
    }
    
    return matchesKeyword && matchesType && matchesLocation && matchesStatus && matchesTimeRange && matchesDuration
  })
})

// 计算活动时长
const calculateDuration = (activity) => {
  if (!activity.batches || activity.batches.length === 0) return 0
  const batch = activity.batches[0]
  const start = new Date(batch.start_time)
  const end = new Date(batch.end_time)
  return (end - start) / (1000 * 60 * 60)
}

// 获取名额百分比
const getQuotaPercentage = (activity) => {
  if (!activity.total_quota || activity.total_quota === 0) return 0
  return Math.round((activity.total_apply_count / activity.total_quota) * 100)
}

// 获取名额颜色
const getQuotaColor = (activity) => {
  const percentage = getQuotaPercentage(activity)
  if (percentage >= 90) return '#f56c6c'
  if (percentage >= 70) return '#e6a23c'
  return '#67c23a'
}

// 获取类型颜色
const getTypeColor = (type) => {
  const colorMap = {
    campus: 'primary',
    community: 'success',
    environment: 'warning',
    other: 'info'
  }
  return colorMap[type] || 'info'
}

// 获取类型文本
const getTypeText = (type) => {
  const textMap = {
    campus: '校园服务',
    community: '社区服务',
    environment: '环保活动',
    other: '其他'
  }
  return textMap[type] || type
}

// 加载活动列表
const loadActivities = async () => {
  try {
    loading.value = true
    const res = await activityAPI.getList()
    // 处理分页数据
    activities.value = res.results || res
    console.log('活动列表数据:', activities.value)
    if (activities.value && activities.value.length > 0) {
      console.log('第一个活动的批次数据:', activities.value[0].batches)
    }
  } catch (error) {
    ElMessage.error('加载活动列表失败')
  } finally {
    loading.value = false
  }
}

// 显示报名对话框
const showApplyDialog = (activity) => {
  selectedActivity.value = activity
  showApplyDialogVisible.value = true
}

// 确认报名
const confirmApply = async (batchId) => {
  try {
    await activityAPI.apply(selectedActivity.value.id, batchId)
    ElMessage.success('报名成功！')
    showApplyDialogVisible.value = false
    loadActivities()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '报名失败')
  }
}

// 查看详情
const viewDetail = (activity) => {
  selectedActivity.value = activity
  showDetailDialogVisible.value = true
}

// 发布活动
const createActivity = async () => {
  try {
    await activityAPI.create(newActivity.value)
    ElMessage.success('活动创建成功！')
    showCreateDialog.value = false
    loadActivities()
  } catch (error) {
    ElMessage.error('创建活动失败')
  }
}

// 编辑活动
const editActivity = (activity) => {
  ElMessage.info('编辑功能开发中...')
}

// 删除活动
const deleteActivity = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个活动吗？', '提示', {
      type: 'warning'
    })
    await activityAPI.delete(id)
    ElMessage.success('删除成功')
    loadActivities()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 工具函数
const getStatusText = (status) => {
  const statusMap = {
    draft: '草稿',
    published: '已发布',
    ongoing: '进行中',
    ended: '已结束',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    published: 'success',
    ongoing: 'warning',
    ended: 'info',
    cancelled: 'danger'
  }
  return typeMap[status] || 'info'
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activity-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.batch-time {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.more-batches {
  font-size: 12px;
  color: #409eff;
  cursor: pointer;
}

.quota-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-state {
  margin-top: 40px;
}
</style>