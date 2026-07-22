import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Popup, Switch } from 'vant'
import 'vant/es/dialog/style'
import 'vant/es/popup/style'
import 'vant/es/switch/style'
import 'vant/es/toast/style'
import './style.css'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
void useAuthStore(pinia).restoreSession()
app.use(router)
app.use(Popup)
app.use(Switch)
app.mount('#app')
