import { createRouter, createWebHistory } from 'vue-router'
import KnowledgeBase from '../views/KnowledgeBase.vue'

const routes = [
  {
    path: '/',
    name: 'knowledge-base',
    component: KnowledgeBase
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

export default router
