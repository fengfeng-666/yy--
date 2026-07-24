<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, reactive, ref } from 'vue'
import { closeToast, showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'
import { ChevronRight, ImagePlus, Pencil, Plus, Search, Trash2, Utensils } from 'lucide-vue-next'

import { useDishStore } from '@/stores/dish'
import { useFamilyStore } from '@/stores/family'
import type { DishItem } from '@/types/dish'
import { resolveAssetUrl } from '@/utils/assets'
import NoFamilyState from '@/components/NoFamilyState.vue'

const router = useRouter()
const dishStore = useDishStore()
const familyStore = useFamilyStore()
const { dishes, loading } = storeToRefs(dishStore)
const { hasFamily } = storeToRefs(familyStore)

const isDishPopupVisible = ref(false)
const isSubmittingDish = ref(false)
const isUploadingImage = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const searchText = ref('')

const dishForm = reactive({
  id: null as number | null,
  name: '',
  description: '',
  priceText: '',
  imageUrl: '',
  isAvailable: true,
})

const dishPopupTitle = computed(() => (dishForm.id ? '编辑菜品' : '新增菜品'))
const currentImagePreview = computed(() => resolveAssetUrl(dishForm.imageUrl))
const filteredDishes = computed(() => {
  const keyword = searchText.value.trim().toLocaleLowerCase()
  if (!keyword) return dishes.value
  return dishes.value.filter((dish) =>
    `${dish.name} ${dish.description ?? ''}`.toLocaleLowerCase().includes(keyword),
  )
})

function resetDishForm() {
  dishForm.id = null
  dishForm.name = ''
  dishForm.description = ''
  dishForm.priceText = ''
  dishForm.imageUrl = ''
  dishForm.isAvailable = true
}

onMounted(async () => {
  if (!hasFamily.value) {
    return
  }
  try {
    await dishStore.initialize()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载菜品失败')
  }
})

function openCreateDish() {
  resetDishForm()
  isDishPopupVisible.value = true
}

function openEditDish(dish: DishItem) {
  dishForm.id = dish.id
  dishForm.name = dish.name
  dishForm.description = dish.description ?? ''
  dishForm.priceText = dish.price.toFixed(2)
  dishForm.imageUrl = dish.image_url ?? ''
  dishForm.isAvailable = dish.is_available
  isDishPopupVisible.value = true
}

async function submitDishForm() {
  if (!dishForm.name.trim()) {
    showFailToast('请输入菜品名称')
    return
  }

  const price = Number(dishForm.priceText)
  if (Number.isNaN(price) || price < 0) {
    showFailToast('请输入正确的价格')
    return
  }

  isSubmittingDish.value = true
  try {
    const payload = {
      name: dishForm.name.trim(),
      description: dishForm.description.trim() || undefined,
      price,
      image_url: dishForm.imageUrl || undefined,
      is_available: dishForm.isAvailable,
    }

    if (dishForm.id) {
      await dishStore.updateDishItem(dishForm.id, payload)
      showSuccessToast('菜品已更新')
    } else {
      await dishStore.createDishItem(payload)
      showSuccessToast('菜品已创建')
    }
    isDishPopupVisible.value = false
    resetDishForm()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '保存菜品失败')
  } finally {
    isSubmittingDish.value = false
  }
}

async function handleDeleteDish(dish: DishItem) {
  try {
    await showConfirmDialog({
      title: '删除菜品',
      message: `确认删除「${dish.name}」吗？`,
    })
    await dishStore.removeDishItem(dish.id)
    showSuccessToast('菜品已删除')
  } catch (error) {
    if (error instanceof Error) {
      showFailToast(error.message)
    }
  }
}

function triggerImageUpload() {
  fileInputRef.value?.click()
}

async function handleImageChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) {
    return
  }

  isUploadingImage.value = true
  try {
    const uploadResult = await dishStore.uploadImage(file)
    dishForm.imageUrl = uploadResult.path
    showSuccessToast('图片上传成功')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '图片上传失败')
  } finally {
    isUploadingImage.value = false
    input.value = ''
    closeToast()
  }
}

function formatPrice(price: number) {
  return `¥ ${price.toFixed(2)}`
}

async function openDishDetail(dishId: number) {
  await router.push(`/dishes/${dishId}`)
}
</script>

<template>
  <section class="yy-page space-y-5 pb-8 pt-5">
    <header class="yy-enter flex items-end justify-between gap-4 px-1">
      <div>
        <p class="yy-kicker">Family menu</p>
        <h1 class="yy-display mt-2 text-[32px] font-bold leading-none text-[var(--yy-ink)]">今天想吃什么</h1>
        <p class="mt-3 text-sm text-[var(--yy-muted)]">把你们的拿手菜，慢慢攒成一本家庭菜单。</p>
      </div>
      <button
        v-if="hasFamily"
        type="button"
        class="yy-primary-button flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[var(--yy-ink)] text-white shadow-[0_12px_25px_rgba(48,37,31,0.2)]"
        aria-label="新增菜品"
        @click="openCreateDish"
      >
        <Plus class="h-5 w-5" />
      </button>
    </header>

    <NoFamilyState
      v-if="!hasFamily"
      title="加入家庭后查看共享菜单"
      description="家庭菜单由成员共同维护。加入或创建家庭后，就可以开始添加拿手菜。"
    />

    <template v-else>
    <div class="yy-card yy-enter yy-enter-delay-1 flex items-center gap-3 px-4 py-3.5">
      <Search class="h-5 w-5 shrink-0 text-[var(--yy-muted)]" aria-hidden="true" />
      <input
        v-model="searchText"
        type="search"
        placeholder="搜索菜名或描述"
        class="min-w-0 flex-1 bg-transparent text-sm text-[var(--yy-ink)] outline-none placeholder:text-[var(--yy-muted)]/70"
        aria-label="搜索菜品"
      />
      <span class="shrink-0 rounded-full bg-[var(--yy-cream)] px-2.5 py-1 text-[11px] text-[var(--yy-muted)]">
        {{ filteredDishes.length }} 道
      </span>
    </div>

    <div v-if="loading" class="yy-card p-8 text-center text-sm text-[var(--yy-muted)]">
      正在加载菜品...
    </div>

    <div v-else-if="!filteredDishes.length" class="yy-card p-8 text-center">
      <span class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#fff0e3] text-[var(--yy-tomato)]">
        <Utensils class="h-6 w-6" />
      </span>
      <p class="yy-display mt-4 text-xl font-bold text-[var(--yy-ink)]">
        {{ searchText ? '没有找到这道菜' : '还没有菜品' }}
      </p>
      <p class="mt-2 text-sm leading-6 text-[var(--yy-muted)]">
        {{ searchText ? '换个关键词试试看。' : '把常做菜录进家庭菜单，之后点菜会更方便。' }}
      </p>
      <button
        v-if="!searchText"
        type="button"
        class="yy-primary-button mt-5 rounded-full bg-[var(--yy-ink)] px-5 py-2.5 text-sm text-white"
        @click="openCreateDish"
      >
        现在添加
      </button>
    </div>

    <div v-else class="space-y-3">
      <article
        v-for="dish in filteredDishes"
        :key="dish.id"
        class="yy-card group overflow-hidden p-3 transition hover:-translate-y-0.5 hover:shadow-[0_22px_55px_rgba(77,53,38,0.13)]"
      >
        <div class="flex gap-4">
          <button
            type="button"
            class="h-[118px] w-[118px] shrink-0 overflow-hidden rounded-[22px] bg-[var(--yy-cream)]"
            :aria-label="`查看${dish.name}详情`"
            @click="openDishDetail(dish.id)"
          >
            <img
              v-if="dish.image_url"
              :src="resolveAssetUrl(dish.image_url)"
              :alt="dish.name"
              class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
            />
            <span
              v-else
              class="flex h-full w-full items-center justify-center bg-[linear-gradient(135deg,_#f8dcc2,_#efb08c)] text-white/80"
            >
              <Utensils class="h-8 w-8" />
            </span>
          </button>

          <div class="min-w-0 flex-1 py-1">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <h2 class="truncate text-lg font-semibold text-[var(--yy-ink)]">{{ dish.name }}</h2>
                <p class="mt-1 text-base font-semibold text-[var(--yy-tomato)]">{{ formatPrice(dish.price) }}</p>
              </div>
              <span
                class="shrink-0 rounded-full px-2.5 py-1 text-[10px] font-medium"
                :class="
                  dish.is_available
                    ? 'bg-[#edf2e9] text-[#627459]'
                    : 'bg-slate-100 text-slate-500'
                "
              >
                {{ dish.is_available ? '上架中' : '已下架' }}
              </span>
            </div>
            <p class="mt-2 line-clamp-2 text-xs leading-5 text-[var(--yy-muted)]">
              {{ dish.description || '这道菜还没有补充描述。' }}
            </p>
            <div class="mt-3 flex items-center gap-2">
              <button
                type="button"
                class="yy-icon-button flex h-8 w-8 items-center justify-center rounded-full bg-[var(--yy-cream)] text-[var(--yy-ink)]"
                :aria-label="`编辑${dish.name}`"
                @click="openEditDish(dish)"
              >
                <Pencil class="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                class="yy-icon-button flex h-8 w-8 items-center justify-center rounded-full bg-red-50 text-red-500"
                :aria-label="`删除${dish.name}`"
                @click="handleDeleteDish(dish)"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                class="ml-auto inline-flex items-center gap-1 text-xs font-medium text-[var(--yy-muted)]"
                @click="openDishDetail(dish.id)"
              >
                详情 <ChevronRight class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </article>
    </div>

    <van-popup
      v-model:show="isDishPopupVisible"
      round
      position="bottom"
      :style="{ maxWidth: '430px', margin: '0 auto', width: '100%', padding: '20px 20px 28px' }"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-[var(--yy-ink)]">{{ dishPopupTitle }}</h3>
          <button
            type="button"
            class="text-sm text-[var(--yy-muted)]"
            @click="isDishPopupVisible = false"
          >
            关闭
          </button>
        </div>

        <input
          v-model.trim="dishForm.name"
          type="text"
          placeholder="菜品名称"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
        />

        <input
          v-model.trim="dishForm.priceText"
          type="number"
          min="0"
          step="0.01"
          placeholder="价格，例如 28.00"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
        />

        <textarea
          v-model.trim="dishForm.description"
          rows="4"
          placeholder="菜品描述，可选"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
        ></textarea>

        <div class="rounded-[24px] border border-dashed border-[var(--yy-line)] p-4">
          <div
            v-if="currentImagePreview"
            class="mb-3 aspect-[4/3] overflow-hidden rounded-[18px] bg-[var(--yy-cream)]"
          >
            <img :src="currentImagePreview" alt="菜品图片" class="h-full w-full object-cover" />
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            class="hidden"
            @change="handleImageChange"
          />
          <div class="flex items-center justify-between gap-3">
            <div class="text-sm text-[var(--yy-muted)]">
              {{ dishForm.imageUrl ? '已上传图片，可继续更换' : '支持 JPG、PNG、WEBP' }}
            </div>
            <button
              type="button"
              class="rounded-full bg-white px-4 py-2 text-sm text-[var(--yy-ink)] shadow-sm"
              :disabled="isUploadingImage"
              @click="triggerImageUpload"
            >
              <ImagePlus class="mr-1 inline h-4 w-4" />
              {{ isUploadingImage ? '上传中...' : '上传图片' }}
            </button>
          </div>
        </div>

        <label class="flex items-center justify-between rounded-2xl bg-[var(--yy-cream)] px-4 py-3">
          <span class="text-sm text-[var(--yy-ink)]">是否上架</span>
          <van-switch v-model="dishForm.isAvailable" size="22" />
        </label>

        <button
          type="button"
          class="w-full rounded-full bg-[var(--yy-ink)] px-5 py-3 text-sm font-medium text-white"
          :disabled="isSubmittingDish"
          @click="submitDishForm"
        >
          {{ isSubmittingDish ? '保存中...' : '保存菜品' }}
        </button>
      </div>
    </van-popup>
    </template>
  </section>
</template>
