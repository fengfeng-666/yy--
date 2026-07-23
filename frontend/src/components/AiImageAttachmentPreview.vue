<script setup lang="ts">
import { X } from 'lucide-vue-next'

defineProps<{
  fileName: string
  previewUrl: string
}>()

defineEmits<{
  remove: []
}>()
</script>

<template>
  <div class="rounded-[24px] border border-[var(--yy-line)] bg-white/90 p-3 shadow-sm">
    <div class="flex items-start gap-3">
      <img :src="previewUrl" :alt="fileName" class="h-20 w-20 rounded-2xl object-cover" />
      <div class="min-w-0 flex-1">
        <p class="text-xs uppercase tracking-[0.16em] text-[var(--yy-muted)]">冰箱图片</p>
        <p class="mt-2 truncate text-sm font-medium text-[var(--yy-ink)]">{{ fileName }}</p>
        <p class="mt-1 text-xs leading-5 text-[var(--yy-muted)]">发送后 AI 会结合图片内容和文字一起推荐菜品。</p>
      </div>
      <button
        type="button"
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--yy-cream)] text-[var(--yy-muted)] transition hover:text-[var(--yy-ink)]"
        aria-label="移除图片"
        @click="$emit('remove')"
      >
        <X class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
