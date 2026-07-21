<template>
  <section class="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(242,172,114,0.18),_transparent_42%),_var(--yy-cream)] px-6 py-10">
    <div class="w-full max-w-[380px] rounded-[32px] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(87,64,46,0.12)] backdrop-blur">
      <p class="text-sm font-medium tracking-[0.3em] text-[var(--yy-muted)]">YY KITCHEN</p>
      <h1 class="mt-4 text-3xl font-semibold text-[var(--yy-ink)]">两个人的私厨餐桌</h1>
      <p class="mt-3 text-sm leading-6 text-[var(--yy-muted)]">
        使用用户名和密码登录，继续记录今天吃什么、谁来做、吃得怎么样。
      </p>

      <div class="mt-8 space-y-4">
        <div class="rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-muted)]">
          用户名
        </div>
        <div class="rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm text-[var(--yy-muted)]">
          密码
        </div>
      </div>

      <button
        type="button"
        class="mt-6 w-full rounded-full bg-[var(--yy-ink)] px-5 py-3 text-sm font-medium text-white transition hover:opacity-90"
      >
        进入 YY 私厨
      </button>

      <div class="mt-5 flex items-center justify-between text-sm text-[var(--yy-muted)]">
        <span>注册入口占位</span>
        <span>忘记密码占位</span>
      </div>
    </div>
  </section>
</template>
