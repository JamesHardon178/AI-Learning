import { createRouter, createWebHistory } from "vue-router"
import Login from "../views/Login.vue"
import Chat from "../views/Chat.vue"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      redirect: () => (localStorage.getItem("token") ? "/chat" : "/login")
    },
    {
      path: "/login",
      name: "login",
      component: Login,
      meta: { guestOnly: true }
    },
    {
      path: "/chat",
      name: "chat",
      component: Chat,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to) => {
  const hasToken = Boolean(localStorage.getItem("token"))

  if (to.meta.requiresAuth && !hasToken) {
    return {
      name: "login",
      query: { redirect: to.fullPath }
    }
  }

  if (to.meta.guestOnly && hasToken) {
    return { name: "chat" }
  }

  return true
})

export default router
