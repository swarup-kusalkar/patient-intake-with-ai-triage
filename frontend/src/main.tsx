import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import App from './App.tsx'
import './index.css'

// ---------------------------------------------------------------------------
// QueryClient configuration
// - staleTime: 30s — prevents redundant refetches on rapid navigation
// - retry: 1 — one retry on failure; prevents retry-storms on real errors
// ---------------------------------------------------------------------------
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,  // 30 seconds
      retry: 1,
    },
    mutations: {
      retry: 0,  // Don't retry mutations — they may have side effects
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
      {/* ReactQueryDevtools only rendered in development builds */}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>,
)
