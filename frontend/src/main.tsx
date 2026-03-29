import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { setupApiInterceptors } from './services/api'
import { useAuthStore } from './store/auth'

setupApiInterceptors(
  () => useAuthStore.getState().token,
  () => {
    const authState = useAuthStore.getState()
    if (!authState.token) {
      return
    }

    authState.clearAuth()

    if (window.location.pathname !== '/login') {
      window.location.assign('/login')
    }
  },
)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
