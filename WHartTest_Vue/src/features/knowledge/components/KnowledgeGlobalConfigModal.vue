<template>
  <a-modal
    :visible="visible"
    title="知识库全局配置"
    :width="modalWidth"
    @ok="handleSubmit"
    @cancel="handleCancel"
    :confirm-loading="loading"
    :modal-style="{ maxWidth: '95vw' }"
  >
    <a-spin :loading="fetchLoading">
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
      >
        <a-alert type="info">
          全局配置将应用于所有知识库向量生成，修改后新上传的文档将使用新配置。
        </a-alert>

        <a-divider>嵌入服务配置</a-divider>

        <a-row :gutter="16">
          <a-col :xs="24" :sm="12">
            <a-form-item label="嵌入服务" field="embedding_service">
              <a-select
                v-model="formData.embedding_service"
                placeholder="请选择嵌入服务"
                @change="handleEmbeddingServiceChange"
              >
                <a-option
                  v-for="service in embeddingServices"
                  :key="service.value"
                  :value="service.value"
                  :label="service.label"
                />
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="模型名称" field="model_name">
              <a-input
                v-model="formData.model_name"
                placeholder="text-embedding-ada-002 / bge-m3"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="API基础URL" field="api_base_url">
          <a-input
            v-model="formData.api_base_url"
            placeholder="http://your-embedding-service.com/v1/embeddings"
          />
        </a-form-item>

        <a-row :gutter="16" align="end">
          <a-col :xs="24" :sm="16">
            <a-form-item label="API密钥" field="api_key">
              <a-input-password
                v-model="formData.api_key"
                placeholder="OpenAI/Azure必填，Ollama/自定义可选"
              />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="8">
            <a-form-item>
              <a-button
                @click="testEmbeddingService"
                :loading="testingConnection"
                type="outline"
                long
              >
                <template #icon><icon-refresh /></template>
                测试连接
              </a-button>
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider>默认分块配置</a-divider>

        <a-row :gutter="16">
          <a-col :xs="24" :sm="12">
            <a-form-item field="chunk_size">
              <template #label>
                分块大小
                <a-tooltip content="每个文本块的最大字符数。建议值1000-2000，较小值提高检索精度，较大值保持上下文完整性。">
                  <icon-question-circle class="label-tip-icon" />
                </a-tooltip>
              </template>
              <a-input-number
                v-model="formData.chunk_size"
                placeholder="分块大小"
                :min="100"
                :max="4000"
                :step="100"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item field="chunk_overlap">
              <template #label>
                分块重叠
                <a-tooltip content="相邻文本块之间的重叠字符数。建议为分块大小的10-20%，可避免跨块信息丢失。">
                  <icon-question-circle class="label-tip-icon" />
                </a-tooltip>
              </template>
              <a-input-number
                v-model="formData.chunk_overlap"
                placeholder="分块重叠"
                :min="0"
                :max="500"
                :step="50"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <div v-if="formData.updated_by_name" class="config-meta">
          <a-space>
            <span>最后更新：{{ formData.updated_by_name }}</span>
            <span>{{ formatDate(formData.updated_at) }}</span>
          </a-space>
        </div>
      </a-form>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue';
import { Message } from '@arco-design/web-vue';
import { IconRefresh, IconQuestionCircle } from '@arco-design/web-vue/es/icon';
import { KnowledgeService } from '../services/knowledgeService';
import type {
  KnowledgeGlobalConfig,
  EmbeddingServiceType,
  EmbeddingServiceOption
} from '../types/knowledge';
import { getRequiredFieldsForEmbeddingService } from '../types/knowledge';

interface Props {
  visible: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
  saved: [];
}>();

const formRef = ref();
const loading = ref(false);
const fetchLoading = ref(false);
const testingConnection = ref(false);

// 窗口宽度响应式
const windowWidth = ref(window.innerWidth);
const updateWindowWidth = () => { windowWidth.value = window.innerWidth; };
const modalWidth = computed(() => windowWidth.value < 600 ? '95%' : 580);

onMounted(() => window.addEventListener('resize', updateWindowWidth));
onUnmounted(() => window.removeEventListener('resize', updateWindowWidth));

// 表单数据
const formData = reactive<KnowledgeGlobalConfig>({
  embedding_service: 'custom',
  api_base_url: '',
  api_key: '',
  model_name: '',
  chunk_size: 1000,
  chunk_overlap: 200,
  updated_at: '',
  updated_by_name: '',
});

// 嵌入服务选项
const embeddingServices = ref<EmbeddingServiceOption[]>([]);

// 动态表单验证规则
const rules = computed(() => {
  const baseRules: any = {
    embedding_service: [
      { required: true, message: '请选择嵌入服务' },
    ],
    api_base_url: [
      { required: true, message: '请输入API基础URL' },
    ],
    model_name: [
      { required: true, message: '请输入模型名称' },
    ],
    chunk_size: [
      { required: true, message: '请输入分块大小' },
      { type: 'number', min: 100, max: 4000, message: '分块大小必须在100-4000之间' },
    ],
    chunk_overlap: [
      { required: true, message: '请输入分块重叠' },
      { type: 'number', min: 0, max: 500, message: '分块重叠必须在0-500之间' },
    ],
  };

  const requiredFields = getRequiredFieldsForEmbeddingService(formData.embedding_service || '');
  if (requiredFields.includes('api_key')) {
    baseRules.api_key = [{ required: true, message: '请输入API密钥' }];
  }

  return baseRules;
});

// 监听弹窗显示状态
watch(() => props.visible, async (visible) => {
  if (visible) {
    await fetchData();
  }
});

// 获取数据
const fetchData = async () => {
  fetchLoading.value = true;
  try {
    // 获取嵌入服务选项
    const servicesResponse = await KnowledgeService.getEmbeddingServices();
    embeddingServices.value = servicesResponse.services;

    // 获取当前配置
    const config = await KnowledgeService.getGlobalConfig();
    Object.assign(formData, config);
  } catch (error) {
    console.error('获取配置失败:', error);
    Message.error('获取配置失败');
  } finally {
    fetchLoading.value = false;
  }
};

// 处理嵌入服务变化
const handleEmbeddingServiceChange = (value: EmbeddingServiceType) => {
  switch (value) {
    case 'openai':
      formData.api_base_url = 'https://api.openai.com/v1/embeddings';
      formData.model_name = 'text-embedding-ada-002';
      break;
    case 'azure_openai':
      formData.api_base_url = 'https://your-resource.openai.azure.com/';
      formData.model_name = 'text-embedding-ada-002';
      break;
    case 'ollama':
      formData.api_base_url = 'http://localhost:8917';
      formData.model_name = 'bge-m3';
      formData.api_key = '';
      break;
    case 'custom':
      formData.api_base_url = 'http://your-embedding-service:8080/v1/embeddings';
      formData.model_name = 'bge-m3';
      break;
  }
};

// 测试嵌入服务连接
const testEmbeddingService = async () => {
  if (!formData.embedding_service || !formData.api_base_url || !formData.model_name) {
    Message.warning('请先完成嵌入服务配置');
    return;
  }
  
  const needsApiKey = formData.embedding_service === 'openai' || formData.embedding_service === 'azure_openai';
  if (needsApiKey && !formData.api_key) {
    Message.warning('此服务需要API密钥');
    return;
  }

  testingConnection.value = true;
  try {
    // 通过后端代理测试，避免跨域问题
    const result = await KnowledgeService.testEmbeddingConnection({
      embedding_service: formData.embedding_service,
      api_base_url: formData.api_base_url,
      api_key: formData.api_key || '',
      model_name: formData.model_name,
    });
    
    if (result.success) {
      Message.success(result.message || '嵌入模型测试成功！服务运行正常');
    } else {
      Message.error(result.message || '测试失败');
    }
  } catch (error: any) {
    Message.error(error?.message || '无法连接到服务');
  } finally {
    testingConnection.value = false;
  }
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('zh-CN');
};

const handleSubmit = async () => {
  try {
    await formRef.value?.validate();
    loading.value = true;

    await KnowledgeService.updateGlobalConfig({
      embedding_service: formData.embedding_service,
      api_base_url: formData.api_base_url,
      api_key: formData.api_key,
      model_name: formData.model_name,
      chunk_size: formData.chunk_size,
      chunk_overlap: formData.chunk_overlap,
    });

    Message.success('配置保存成功');
    emit('saved');
    emit('close');
  } catch (error: any) {
    console.error('保存配置失败:', error);
    Message.error(error?.message || '保存配置失败');
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  emit('close');
};
</script>

<style scoped>
:deep(.arco-form-item) {
  margin-bottom: 12px;
}

:deep(.arco-divider) {
  margin: 12px 0;
}

:deep(.arco-alert) {
  margin-bottom: 12px !important;
}

.config-meta {
  font-size: 12px;
  color: var(--color-text-3);
  text-align: right;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.label-tip-icon {
  margin-left: 4px;
  color: var(--color-text-3);
  cursor: help;
}
</style>
