<template>
  <section class="space-y-4 px-5 pb-8 pt-6">
    <header>
      <p class="text-sm text-[var(--yy-muted)]">点菜中心</p>
      <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">正在流转的菜单</h1>
    </header>

    <div class="flex gap-2 overflow-x-auto pb-1">
      <span class="rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white">待确认</span>
      <span class="rounded-full bg-white px-4 py-2 text-sm text-[var(--yy-muted)] shadow-sm">已接受</span>
    </div>

    <article class="rounded-[28px] border border-[var(--yy-line)] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-[var(--yy-ink)]">今晚 19:00</h2>
        <span class="rounded-full bg-orange-50 px-3 py-1 text-xs text-orange-700">待确认</span>
      </div>
      <p class="mt-3 text-sm text-[var(--yy-muted)]">老婆向你点了：糖醋排骨、清炒生菜</p>
      <div class="mt-4 flex gap-3">
        <button type="button" class="rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white">接受</button>
        <button type="button" class="rounded-full bg-[var(--yy-cream)] px-4 py-2 text-sm text-[var(--yy-ink)]">修改</button>
        <button type="button" class="rounded-full bg-[var(--yy-tomato)]/12 px-4 py-2 text-sm text-[var(--yy-tomato)]">拒绝</button>
      </div>
    </article>
  </section>
</template>
