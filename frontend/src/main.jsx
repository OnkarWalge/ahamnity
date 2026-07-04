import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import ASHADashboard from './components/ASHADashboard.jsx'
import './index.css'

// Two audiences, two views, no router library needed for just this:
// localhost:5173       -> patient voice interface
// localhost:5173/asha  -> ASHA worker dashboard
const isAshaView = window.location.pathname.startsWith('/asha')

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isAshaView ? <ASHADashboard /> : <App />}
  </React.StrictMode>,
)