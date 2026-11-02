<script setup>
import { ref } from 'vue'
import axios from 'axios'

const goal = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)

const examples = [
  '电脑开机进入 grub rescue 界面，无法启动系统',
  '系统启动卡住，内核日志报 EXT4-fs error',
  '系统报 /boot 挂载失败，无法继续启动'
]

async function repair(text) {
  const g = (text ?? goal.value).trim()
  if (!g) {
    error.value = '请先输入故障描述'
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const { data } = await axios.post('/api/repair', { goal: g })
    if (data.code === 0) {
      result.value = data.data
    } else {
      error.value = data.msg || '未知错误'
    }
  } catch (e) {
    error.value = '请求失败：' + (e.response?.data?.msg || e.message || '后端未启动？')
  } finally {
    loading.value = false
  }
}

function stepType(step) {
  if (step.action === 'finish') return 'success'
  if (step.success === false) return 'danger'
  return 'primary'
}
</script>

<template>
  <div class="page">
    <header class="header">
      <h1>PE-Agent · 系统救援助手</h1>
      <p class="sub">LangGraph + RAG + Skill 框架 · Java 后端 + Python Agent</p>
    </header>

    <main class="container">
      <!-- 输入区 -->
      <el-card class="card">
        <el-input
          v-model="goal"
          type="textarea"
          :rows="3"
          placeholder="描述你遇到的系统故障，例如：电脑开机进入 grub rescue 界面，无法启动系统"
        />
        <div class="actions">
          <div class="examples">
            <el-tag
              v-for="e in examples"
              :key="e"
              class="example-tag"
              @click="goal = e"
            >{{ e.slice(0, 14) }}…</el-tag>
          </div>
          <el-button type="primary" :loading="loading" @click="repair()">
            {{ loading ? '诊断中…' : '开始救援' }}
          </el-button>
        </div>
      </el-card>

      <!-- 错误 -->
      <el-alert v-if="error" :title="error" type="error" show-icon class="mt" />

      <!-- 结果 -->
      <template v-if="result">
        <el-card class="card mt">
          <div class="result-head">
            <el-tag :type="result.finished ? 'success' : 'warning'" size="large">
              {{ result.finished ? '修复完成' : '未完成' }}
            </el-tag>
            <span class="answer">{{ result.finalAnswer || '（无结论）' }}</span>
          </div>
        </el-card>

        <el-card class="card mt" v-if="result.trajectory && result.trajectory.length">
          <template #header>
            <span>执行轨迹（共 {{ result.trajectory.length }} 步）</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(step, i) in result.trajectory"
              :key="i"
              :type="stepType(step)"
              :timestamp="`步骤 ${i + 1}`"
            >
              <strong>{{ step.action }}</strong>
              <div class="step-msg">{{ step.message }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page {
  max-width: 820px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}
.header {
  text-align: center;
  margin-bottom: 20px;
}
.header h1 {
  font-size: 24px;
  font-weight: 600;
}
.sub {
  color: #909399;
  font-size: 13px;
  margin-top: 6px;
}
.card {
  border-radius: 10px;
}
.mt {
  margin-top: 16px;
}
.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
  gap: 12px;
}
.examples {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.example-tag {
  cursor: pointer;
}
.result-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.answer {
  font-size: 14px;
  color: #303133;
}
.step-msg {
  color: #606266;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
