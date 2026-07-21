<template>
  <section class="space-y-4 px-5 pb-8 pt-6">
    <header>
      <p class="text-sm text-[var(--yy-muted)]">家庭菜单</p>
      <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">今天想吃什么</h1>
    </header>

    <div class="flex gap-2 overflow-x-auto pb-1">
      <span class="rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white">全部</span>
      <span class="rounded-full bg-white px-4 py-2 text-sm text-[var(--yy-muted)] shadow-sm">荤菜</span>
      <span class="rounded-full bg-white px-4 py-2 text-sm text-[var(--yy-muted)] shadow-sm">素菜</span>
      <span class="rounded-full bg-white px-4 py-2 text-sm text-[var(--yy-muted)] shadow-sm">30 分钟内</span>
    </div>

    <article class="rounded-[28px] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
      <div class="aspect-[4/3] rounded-[22px] bg-[linear-gradient(135deg,_rgba(242,172,114,0.4),_rgba(232,122,85,0.28))]"></div>
      <div class="mt-4 flex items-start justify-between gap-4">
        <div>
          <h2 class="text-lg font-semibold text-[var(--yy-ink)]">糖醋排骨</h2>
          <p class="mt-1 text-sm text-[var(--yy-muted)]">45 分钟 · 难度 3 · 默认厨师：睿丰</p>
        </div>
        <span class="rounded-full bg-amber-50 px-3 py-1 text-xs text-amber-700">高评分</span>
      </div>
    </article>
  </section>
</template>
