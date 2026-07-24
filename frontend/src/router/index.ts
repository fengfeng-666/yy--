import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

const DishDetailPage = () => import('@/pages/DishDetailPage.vue')
const MainLayout = () => import('@/layouts/MainLayout.vue')
const DishesPage = () => import('@/pages/DishesPage.vue')
const FamilyOnboardingPage = () => import('@/pages/FamilyOnboardingPage.vue')
const HomePage = () => import('@/pages/HomePage.vue')
const LoginPage = () => import('@/pages/LoginPage.vue')
const AiChatPage = () => import('@/pages/AiChatPage.vue')
const FamilyChatPage = () => import('@/pages/FamilyChatPage.vue')
const MessagesHubPage = () => import('@/pages/MessagesHubPage.vue')
const OrderCreatePage = () => import('@/pages/OrderCreatePage.vue')
const OrderDetailPage = () => import('@/pages/OrderDetailPage.vue')
const OrdersPage = () => import('@/pages/OrdersPage.vue')
const PlansPage = () => import('@/pages/PlansPage.vue')
const ProfilePage = () => import('@/pages/ProfilePage.vue')
const ShoppingListsPage = () => import('@/pages/ShoppingListsPage.vue')

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
    meta: { requiresAuth: true },
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
        path: '/journal',
        name: 'journal',
        component: PlansPage,
      },
      {
        path: '/plans',
        redirect: '/journal',
      },
      {
        path: '/messages',
        name: 'messages',
        component: MessagesHubPage,
        meta: { requiresFamily: false },
      },
      {
        path: '/messages/family',
        name: 'family-chat',
        component: FamilyChatPage,
        meta: { requiresFamily: true, hideBottomNav: true },
      },
      {
        path: '/messages/ai',
        name: 'ai-chat',
        component: AiChatPage,
        meta: { requiresFamily: true, hideBottomNav: true, wideLayout: true },
      },
      {
        path: '/profile',
        name: 'profile',
        component: ProfilePage,
        meta: { requiresFamily: false },
      },
    ],
  },
  {
    path: '/dishes/:id',
    name: 'dish-detail',
    component: DishDetailPage,
    meta: { requiresAuth: true, requiresFamily: true },
  },
  {
    path: '/orders/create',
    name: 'order-create',
    component: OrderCreatePage,
    meta: { requiresAuth: true, requiresFamily: true },
  },
  {
    path: '/orders/:id',
    name: 'order-detail',
    component: OrderDetailPage,
    meta: { requiresAuth: true, requiresFamily: true },
  },
  {
    path: '/shopping-lists',
    name: 'shopping-lists',
    component: ShoppingListsPage,
    meta: { requiresAuth: true, requiresFamily: true },
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
    return { name: 'home' }
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
