<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { closeToast, showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'

import { useDishStore } from '@/stores/dish'
import type { DishItem } from '@/types/dish'
import { resolveAssetUrl } from '@/utils/assets'

const router = useRouter()
const dishStore = useDishStore()
const { categories, dishes, loading, selectedCategoryId } = storeToRefs(dishStore)

const isDishPopupVisible = ref(false)
const isCategoryPopupVisible = ref(false)
const isSubmittingDish = ref(false)
const isSubmittingCategory = ref(false)
const isUploadingImage = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const newCategoryForm = reactive({
  name: '',
  sortOrder: 0,
})

const dishForm = reactive({
  id: null as number | null,
  name: '',
  categoryId: null as number | null,
  description: '',
  priceText: '',
  imageUrl: '',
  isAvailable: true,
})

const categoryDrafts = ref<Record<number, { name: string; sortOrder: number }>>({})

const dishPopupTitle = computed(() => (dishForm.id ? '编辑菜品' : '新增菜品'))
const currentImagePreview = computed(() => resolveAssetUrl(dishForm.imageUrl))

function resetDishForm() {
  dishForm.id = null
  dishForm.name = ''
  dishForm.categoryId = categories.value[0]?.id ?? null
  dishForm.description = ''
  dishForm.priceText = ''
  dishForm.imageUrl = ''
  dishForm.isAvailable = true
}

function syncCategoryDrafts() {
  categoryDrafts.value = categories.value.reduce(
    (drafts, category) => {
      drafts[category.id] = {
        name: category.name,
        sortOrder: category.sort_order,
      }
      return drafts
    },
    {} as Record<number, { name: string; sortOrder: number }>,
  )
}

watch(categories, syncCategoryDrafts, { immediate: true })

onMounted(async () => {
  try {
    await dishStore.initialize()
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载菜品失败')
  }
})

async function changeCategory(categoryId: number | null) {
  try {
    await dishStore.loadDishes(categoryId)
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载菜品失败')
  }
}

function openCreateDish() {
  if (!categories.value.length) {
    showFailToast('请先创建菜品分类')
    return
  }
  resetDishForm()
  isDishPopupVisible.value = true
}

function openEditDish(dish: DishItem) {
  dishForm.id = dish.id
  dishForm.name = dish.name
  dishForm.categoryId = dish.category_id
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
  if (!dishForm.categoryId) {
    showFailToast('请选择菜品分类')
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
      category_id: dishForm.categoryId,
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

async function submitNewCategory() {
  if (!newCategoryForm.name.trim()) {
    showFailToast('请输入分类名称')
    return
  }

  isSubmittingCategory.value = true
  try {
    await dishStore.createCategory({
      name: newCategoryForm.name.trim(),
      sort_order: newCategoryForm.sortOrder || categories.value.length + 1,
    })
    newCategoryForm.name = ''
    newCategoryForm.sortOrder = 0
    showSuccessToast('分类已创建')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '创建分类失败')
  } finally {
    isSubmittingCategory.value = false
  }
}

async function saveCategory(categoryId: number) {
  const draft = categoryDrafts.value[categoryId]
  if (!draft?.name.trim()) {
    showFailToast('分类名称不能为空')
    return
  }

  try {
    await dishStore.editCategory(categoryId, {
      name: draft.name.trim(),
      sort_order: draft.sortOrder || 0,
    })
    showSuccessToast('分类已更新')
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '更新分类失败')
  }
}

async function deleteCategoryItem(categoryId: number) {
  const currentCategory = categories.value.find((item) => item.id === categoryId)
  if (!currentCategory) {
    return
  }

  try {
    await showConfirmDialog({
      title: '删除分类',
      message: `确认删除「${currentCategory.name}」吗？`,
    })
    await dishStore.removeCategory(categoryId)
    showSuccessToast('分类已删除')
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
  <section class="space-y-4 px-5 pb-8 pt-6">
    <header class="flex items-start justify-between gap-4">
      <div>
        <p class="text-sm text-[var(--yy-muted)]">家庭菜单</p>
        <h1 class="mt-1 text-2xl font-semibold text-[var(--yy-ink)]">今天想吃什么</h1>
        <p class="mt-2 text-sm text-[var(--yy-muted)]">支持分类管理、菜品增删改和图片上传。</p>
      </div>
      <button
        type="button"
        class="rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white"
        @click="openCreateDish"
      >
        新增菜品
      </button>
    </header>

    <div class="flex items-center gap-2 overflow-x-auto pb-1">
      <button
        type="button"
        class="whitespace-nowrap rounded-full px-4 py-2 text-sm transition"
        :class="
          selectedCategoryId === null
            ? 'bg-[var(--yy-ink)] text-white'
            : 'bg-white text-[var(--yy-muted)] shadow-sm'
        "
        @click="changeCategory(null)"
      >
        全部
      </button>
      <button
        v-for="category in categories"
        :key="category.id"
        type="button"
        class="whitespace-nowrap rounded-full px-4 py-2 text-sm transition"
        :class="
          selectedCategoryId === category.id
            ? 'bg-[var(--yy-ink)] text-white'
            : 'bg-white text-[var(--yy-muted)] shadow-sm'
        "
        @click="changeCategory(category.id)"
      >
        {{ category.name }}
      </button>
      <button
        type="button"
        class="whitespace-nowrap rounded-full border border-[var(--yy-line)] bg-white px-4 py-2 text-sm text-[var(--yy-ink)]"
        @click="isCategoryPopupVisible = true"
      >
        管理分类
      </button>
    </div>

    <div class="rounded-[24px] bg-white px-4 py-3 text-sm text-[var(--yy-muted)] shadow-sm">
      共 {{ dishes.length }} 道菜，{{ categories.length }} 个分类
    </div>

    <div v-if="loading" class="rounded-[28px] bg-white p-8 text-center text-sm text-[var(--yy-muted)]">
      正在加载菜品...
    </div>

    <div v-else-if="!dishes.length" class="rounded-[28px] bg-white p-8 text-center shadow-sm">
      <p class="text-lg font-medium text-[var(--yy-ink)]">还没有菜品</p>
      <p class="mt-2 text-sm text-[var(--yy-muted)]">先创建分类，再把常做菜录进家庭菜单。</p>
      <button
        type="button"
        class="mt-5 rounded-full bg-[var(--yy-ink)] px-5 py-2 text-sm text-white"
        @click="openCreateDish"
      >
        现在添加
      </button>
    </div>

    <div v-else class="space-y-4">
      <article
        v-for="dish in dishes"
        :key="dish.id"
        class="rounded-[28px] bg-white p-5 shadow-[0_16px_40px_rgba(87,64,46,0.06)]"
      >
        <div
          v-if="dish.image_url"
          class="aspect-[4/3] overflow-hidden rounded-[22px] bg-[var(--yy-cream)]"
        >
          <img
            :src="resolveAssetUrl(dish.image_url)"
            :alt="dish.name"
            class="h-full w-full object-cover"
          />
        </div>
        <div
          v-else
          class="aspect-[4/3] rounded-[22px] bg-[linear-gradient(135deg,_rgba(242,172,114,0.4),_rgba(232,122,85,0.28))]"
        ></div>

        <div class="mt-4 flex items-start justify-between gap-4">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-lg font-semibold text-[var(--yy-ink)]">{{ dish.name }}</h2>
              <span class="rounded-full bg-[var(--yy-cream)] px-3 py-1 text-xs text-[var(--yy-muted)]">
                {{ dish.category.name }}
              </span>
              <span
                class="rounded-full px-3 py-1 text-xs"
                :class="
                  dish.is_available
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-slate-100 text-slate-500'
                "
              >
                {{ dish.is_available ? '上架中' : '已下架' }}
              </span>
            </div>
            <p class="mt-2 text-base font-medium text-[var(--yy-ink)]">{{ formatPrice(dish.price) }}</p>
            <p class="mt-2 text-sm leading-6 text-[var(--yy-muted)]">
              {{ dish.description || '这道菜还没有补充描述。' }}
            </p>
          </div>

          <div class="flex flex-col gap-2">
            <button
              type="button"
              class="rounded-full bg-[var(--yy-cream)] px-4 py-2 text-xs text-[var(--yy-ink)]"
              @click="openDishDetail(dish.id)"
            >
              详情
            </button>
            <button
              type="button"
              class="rounded-full bg-[var(--yy-ink)] px-4 py-2 text-xs text-white"
              @click="openEditDish(dish)"
            >
              编辑
            </button>
            <button
              type="button"
              class="rounded-full bg-red-50 px-4 py-2 text-xs text-red-600"
              @click="handleDeleteDish(dish)"
            >
              删除
            </button>
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

        <select
          v-model.number="dishForm.categoryId"
          class="w-full rounded-2xl border border-[var(--yy-line)] bg-[var(--yy-cream)] px-4 py-3 text-sm outline-none"
        >
          <option :value="null" disabled>请选择分类</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>

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

    <van-popup
      v-model:show="isCategoryPopupVisible"
      round
      position="bottom"
      :style="{ maxWidth: '430px', margin: '0 auto', width: '100%', padding: '20px 20px 28px' }"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-[var(--yy-ink)]">菜品分类</h3>
          <button
            type="button"
            class="text-sm text-[var(--yy-muted)]"
            @click="isCategoryPopupVisible = false"
          >
            关闭
          </button>
        </div>

        <div class="rounded-[24px] bg-[var(--yy-cream)] p-4">
          <div class="grid grid-cols-[1fr_88px] gap-3">
            <input
              v-model.trim="newCategoryForm.name"
              type="text"
              placeholder="新增分类名称"
              class="rounded-2xl border border-[var(--yy-line)] bg-white px-4 py-3 text-sm outline-none"
            />
            <input
              v-model.number="newCategoryForm.sortOrder"
              type="number"
              min="0"
              placeholder="排序"
              class="rounded-2xl border border-[var(--yy-line)] bg-white px-4 py-3 text-sm outline-none"
            />
          </div>
          <button
            type="button"
            class="mt-3 w-full rounded-full bg-[var(--yy-ink)] px-5 py-3 text-sm font-medium text-white"
            :disabled="isSubmittingCategory"
            @click="submitNewCategory"
          >
            {{ isSubmittingCategory ? '创建中...' : '新增分类' }}
          </button>
        </div>

        <div v-if="!categories.length" class="rounded-2xl bg-[var(--yy-cream)] px-4 py-5 text-center text-sm text-[var(--yy-muted)]">
          还没有分类，先创建一个吧。
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="category in categories"
            :key="category.id"
            class="rounded-[24px] bg-[var(--yy-cream)] p-4"
          >
            <div class="grid grid-cols-[1fr_88px] gap-3">
              <input
                v-model.trim="categoryDrafts[category.id].name"
                type="text"
                class="rounded-2xl border border-[var(--yy-line)] bg-white px-4 py-3 text-sm outline-none"
              />
              <input
                v-model.number="categoryDrafts[category.id].sortOrder"
                type="number"
                min="0"
                class="rounded-2xl border border-[var(--yy-line)] bg-white px-4 py-3 text-sm outline-none"
              />
            </div>
            <div class="mt-3 flex gap-3">
              <button
                type="button"
                class="flex-1 rounded-full bg-[var(--yy-ink)] px-4 py-2 text-sm text-white"
                @click="saveCategory(category.id)"
              >
                保存
              </button>
              <button
                type="button"
                class="flex-1 rounded-full bg-red-50 px-4 py-2 text-sm text-red-600"
                @click="deleteCategoryItem(category.id)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </van-popup>
  </section>
</template>
