<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CalendarDays, House, ScrollText, Soup, UserRound } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const tabs = [
  { name: 'home', label: '首页', path: '/home', icon: House },
  { name: 'dishes', label: '菜单', path: '/dishes', icon: Soup },
  { name: 'orders', label: '点菜', path: '/orders', icon: ScrollText },
  { name: 'plans', label: '计划', path: '/plans', icon: CalendarDays },
  { name: 'profile', label: '我的', path: '/profile', icon: UserRound },
]

const active = computed(() => route.name as string)

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="mx-auto flex min-h-screen w-full max-w-[430px] flex-col bg-[var(--yy-cream)]">
    <main class="flex-1 pb-24">
      <router-view />
    </main>

    <nav class="fixed bottom-0 left-1/2 z-20 flex w-full max-w-[430px] -translate-x-1/2 border-t border-[var(--yy-line)] bg-white/92 px-4 pb-6 pt-3 backdrop-blur">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        type="button"
        class="flex flex-1 flex-col items-center gap-1 rounded-2xl px-2 py-2 text-xs transition"
        :class="
          active === tab.name
            ? 'bg-[var(--yy-apricot)]/20 text-[var(--yy-ink)]'
            : 'text-[var(--yy-muted)] hover:bg-[var(--yy-apricot)]/10'
        "
        @click="navigate(tab.path)"
      >
        <component :is="tab.icon" class="h-5 w-5" />
        <span>{{ tab.label }}</span>
      </button>
    </nav>
  </div>
</template>
