<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpenText, ClipboardList, CookingPot, House, UserRound } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const tabs = [
  { name: 'home', label: '首页', path: '/home', icon: House },
  { name: 'dishes', label: '菜单', path: '/dishes', icon: CookingPot },
  { name: 'orders', label: '点菜', path: '/orders', icon: ClipboardList },
  { name: 'plans', label: '食记', path: '/plans', icon: BookOpenText },
  { name: 'profile', label: '我的', path: '/profile', icon: UserRound },
]

const active = computed(() => route.name as string)

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="yy-shell mx-auto flex min-h-screen w-full max-w-[480px] flex-col">
    <main class="flex-1 pb-[calc(6.75rem+env(safe-area-inset-bottom))]">
      <router-view />
    </main>

    <nav
      aria-label="主导航"
      class="fixed bottom-3 left-1/2 z-20 flex w-[calc(100%-1.5rem)] max-w-[456px] -translate-x-1/2 rounded-[26px] border border-white/70 bg-[rgba(48,37,31,0.94)] px-2 py-2 shadow-[0_18px_50px_rgba(48,37,31,0.28)] backdrop-blur-xl"
      :style="{ paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))' }"
    >
      <button
        v-for="tab in tabs"
        :key="tab.name"
        type="button"
        class="group relative flex min-h-14 flex-1 flex-col items-center justify-center gap-1 rounded-[20px] px-1 text-[11px] transition"
        :class="
          active === tab.name
            ? 'bg-white text-[var(--yy-ink)] shadow-[0_8px_24px_rgba(0,0,0,0.16)]'
            : 'text-white/55 hover:bg-white/8 hover:text-white'
        "
        :aria-current="active === tab.name ? 'page' : undefined"
        @click="navigate(tab.path)"
      >
        <component
          :is="tab.icon"
          class="h-[19px] w-[19px] transition-transform group-hover:-translate-y-0.5"
          :stroke-width="active === tab.name ? 2.3 : 1.8"
        />
        <span class="font-medium">{{ tab.label }}</span>
      </button>
    </nav>
  </div>
</template>
