import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import DishesPage from '@/pages/DishesPage.vue'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import OrdersPage from '@/pages/OrdersPage.vue'
import PlansPage from '@/pages/PlansPage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
  },
  {
    path: '/',
    component: MainLayout,
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

export default router
