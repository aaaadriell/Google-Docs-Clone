// Main Job of this page is to hold routing once we have more than one page
import { BrowserRouter, Routes, Route } from 'react-router'
import LoginPage from './pages/LoginPage.tsx'
import SignupPage from './pages/SignUpPage.tsx'

import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
      </Routes>
    </BrowserRouter>
  )
}
