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
        <el-input v-model="searchKeyword" placeholder="搜索活动名称" style="width: 300px;" clearable />
        <el-select v-model="filterType" placeholder="活动类型" clearable style="margin-left: 10px;">
          <el-option label="校园服务" value="campus" />
          <el-option label="社区服务" value="community" />
          <el-option label="环保活动" value="environment" />
          <el-option label="其他" value="other" />
        </el-select>
        <el-button type="primary" style="margin-left: 10px;" @click="loadActivities">搜索</el-button>
      </div>

      <!-- 活动列表 -->
      <div class="activity-container">
        <div v-for="activity in filteredActivities" :key="activity.id" class="activity-card">
          <div class="activity-header">
            <h3>{{ activity.name }}</h3>
            <el-tag :type="getStatusType(activity.status)">{{ getStatusText(activity.status) }}</el-tag>
          </div>
          <div class="activity-info">
            <p><i class="el-icon-user"></i> 主办方：{{ activity.organizer }}</p>
            <p><i class="el-icon-location"></i> 地点：{{ activity.address }}</p>
            <p><i class="el-icon-time"></i> 创建时间：{{ formatTime(activity.create_time) }}</p>
            <p><i class="el-icon-s-data"></i> 总名额：{{ activity.total_quota }} | 已报名：{{ activity.total_apply_count }}</p>
          </div>
          <div class="activity-batches">
            <h4>活动批次：</h4>
            <div v-for="batch in activity.batches" :key="batch.id" class="batch-item">
              <span>{{ batch.batch_name }}</span>
              <span>时间：{{ formatTime(batch.start_time) }} - {{ formatTime(batch.end_time) }}</span>
              <span>名额：{{ batch.apply_count }}/{{ batch.quota }}</span>
              <el-button v-if="userRole === 'student'" type="primary" size="small" 
                         :disabled="batch.apply_count >= batch.quota"
                         @click="applyActivity(activity.id, batch.id)">
                {{ batch.apply_count >= batch.quota ? '已满' : '报名' }}
              </el-button>
            </div>
          </div>
          <div class="activity-actions">
            <el-button type="primary" link @click="viewDetail(activity.id)">查看详情</el-button>
            <template v-if="userRole === 'teacher'">
              <el-button type="warning" link @click="editActivity(activity)">编辑</el-button>
              <el-button type="danger" link @click="deleteActivity(activity.id)">删除</el-button>
              <el-button v-if="activity.status === 'draft'" type="success" link @click="publishActivity(activity.id)">发布</el-button>
              <el-button v-if="activity.status === 'published'" type="info" link @click="cancelActivity(activity.id)">取消</el-button>
            </template>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredActivities.length === 0" class="empty-state">
        <el-empty description="暂无活动数据" />
      </div>
    </el-card>

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
const showCreateDialog = ref(false)

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
    const matchesKeyword = activity.name.includes(searchKeyword.value)
    const matchesType = !filterType.value || activity.type === filterType.value
    return matchesKeyword && matchesType
  })
})

// 加载活动列表
const loadActivities = async () => {
  try {
    const res = await activityAPI.getList()
    activities.value = res
  } catch (error) {
    ElMessage.error('加载活动列表失败')
  }
}

// 查看详情
const viewDetail = (id) => {
  router.push(`/activity/${id}`)
}

// 报名活动
const applyActivity = async (activityId, batchId) => {
  try {
    await activityAPI.apply(activityId, batchId)
    ElMessage.success('报名成功！')
    loadActivities()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '报名失败')
  }
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

// 发布活动
const publishActivity = async (id) => {
  try {
    await activityAPI.publish(id)
    ElMessage.success('活动发布成功！')
    loadActivities()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '发布失败')
  }
}

// 取消活动
const cancelActivity = async (id) => {
  try {
    await activityAPI.cancel(id)
    ElMessage.success('活动已取消')
    loadActivities()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '取消失败')
  }
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
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}
.activity-container {
  display: grid;
  gap: 20px;
}
.activity-card {
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  padding: 20px;
  background: white;
}
.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.activity-info p {
  margin: 5px 0;
  color: #666;
}
.activity-batches {
  margin: 15px 0;
}
.batch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  margin: 5px 0;
  background: #f8f9fa;
  border-radius: 4px;
}
.activity-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}
.empty-state {
  text-align: center;
  padding: 40px 0;
}
</style>