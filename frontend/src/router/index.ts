import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { storeToRefs } from 'pinia'
import MainLayout from '@/layouts/MainLayout.vue'
import DishesPage from '@/pages/DishesPage.vue'
import FamilyOnboardingPage from '@/pages/FamilyOnboardingPage.vue'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import OrdersPage from '@/pages/OrdersPage.vue'
import PlansPage from '@/pages/PlansPage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { guestOnly: true },
  },
  {
    path: '/family/onboarding',
    name: 'family-onboarding',
    component: FamilyOnboardingPage,
    meta: { requiresAuth: true, allowNoFamily: true },
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true, requiresFamily: true },
    children: [
      {
        path: '',
        redirect: '/home',
      },
      {
        path: '/home',
        name: 'home',
        component: HomePage,
      },
      {
        path: '/dishes',
        name: 'dishes',
        component: DishesPage,
      },
      {
        path: '/orders',
        name: 'orders',
        component: OrdersPage,
      },
      {
        path: '/plans',
        name: 'plans',
        component: PlansPage,
      },
      {
        path: '/profile',
        name: 'profile',
        component: ProfilePage,
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  const familyStore = useFamilyStore()
  const { initialized, isAuthenticated } = storeToRefs(authStore)

  if (!initialized.value) {
    await authStore.restoreSession()
  }

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.guestOnly && isAuthenticated.value) {
    if (!familyStore.initialized) {
      await familyStore.loadCurrentFamily()
    }
    return { name: familyStore.hasFamily ? 'home' : 'family-onboarding' }
  }

  if (isAuthenticated.value && !familyStore.initialized) {
    await familyStore.loadCurrentFamily()
  }

  if (to.meta.requiresFamily && !familyStore.hasFamily) {
    return { name: 'family-onboarding' }
  }

  if (to.meta.allowNoFamily && familyStore.hasFamily) {
    return { name: 'home' }
  }

  return true
})

export default router
