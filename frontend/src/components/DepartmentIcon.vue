<script setup>
import { computed } from 'vue'
import { getDepartmentIconName } from '@/utils/departmentIcons'

const props = defineProps({
  departmentName: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'sm',
  },
  title: {
    type: String,
    default: '',
  },
})

const iconName = computed(() => getDepartmentIconName(props.departmentName))
const titleText = computed(() => props.title || props.departmentName || 'Department')
</script>

<template>
  <span class="department-icon" :class="`size-${size}`" :title="titleText" aria-hidden="true">{{ iconName }}</span>
</template>
