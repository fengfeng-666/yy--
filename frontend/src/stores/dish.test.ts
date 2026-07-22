import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createDish, deleteDish, fetchDishes, updateDish, uploadDishImage } from '@/api/dish'
import { useDishStore } from '@/stores/dish'
import { makeDish } from '@/test/factories'

vi.mock('@/api/dish', () => ({
  createDish: vi.fn(),
  deleteDish: vi.fn(),
  fetchDishes: vi.fn(),
  updateDish: vi.fn(),
  uploadDishImage: vi.fn(),
}))

describe('菜品状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始化只加载一次菜品', async () => {
    vi.mocked(fetchDishes).mockResolvedValue([makeDish()])
    const store = useDishStore()

    await store.initialize()
    await store.initialize()

    expect(fetchDishes).toHaveBeenCalledTimes(1)
    expect(store.initialized).toBe(true)
    expect(store.hasDishes).toBe(true)
  })

  it('加载失败后也会正确结束 loading 状态', async () => {
    vi.mocked(fetchDishes).mockRejectedValue(new Error('network error'))
    const store = useDishStore()

    await expect(store.loadDishes()).rejects.toThrow('network error')

    expect(store.loading).toBe(false)
  })

  it('新增菜品后重新获取最新列表', async () => {
    const dish = makeDish()
    vi.mocked(createDish).mockResolvedValue(dish)
    vi.mocked(fetchDishes).mockResolvedValue([dish])
    const store = useDishStore()

    const result = await store.createDishItem({
      name: dish.name,
      price: dish.price,
      is_available: true,
    })

    expect(result).toEqual(dish)
    expect(fetchDishes).toHaveBeenCalledOnce()
    expect(store.dishes).toEqual([dish])
  })

  it('更新菜品后同步最新列表', async () => {
    const updatedDish = makeDish({ name: '糖醋排骨', price: 38 })
    vi.mocked(updateDish).mockResolvedValue(updatedDish)
    vi.mocked(fetchDishes).mockResolvedValue([updatedDish])
    const store = useDishStore()

    await store.updateDishItem(updatedDish.id, {
      name: updatedDish.name,
      price: updatedDish.price,
      is_available: true,
    })

    expect(store.dishes).toEqual([updatedDish])
  })

  it('删除菜品后从最新列表中移除', async () => {
    vi.mocked(deleteDish).mockResolvedValue(undefined)
    vi.mocked(fetchDishes).mockResolvedValue([])
    const store = useDishStore()
    store.dishes = [makeDish()]

    await store.removeDishItem(1)

    expect(deleteDish).toHaveBeenCalledWith(1)
    expect(store.dishes).toEqual([])
  })

  it('上传图片时返回后端生成的资源地址', async () => {
    const uploadResult = { path: '/uploads/dish.jpg', url: '/uploads/dish.jpg' }
    const file = { name: 'dish.jpg', type: 'image/jpeg' } as File
    vi.mocked(uploadDishImage).mockResolvedValue(uploadResult)
    const store = useDishStore()

    await expect(store.uploadImage(file)).resolves.toEqual(uploadResult)
    expect(uploadDishImage).toHaveBeenCalledWith(file)
  })
})
