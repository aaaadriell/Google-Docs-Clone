// Main Job of this page is to hold routing once we have more than one page
import { BrowserRouter, Routes, Route } from 'react-router'
import LoginPage from './pages/LoginPage.tsx'
import SignUpPage from './pages/SignUpPage.tsx'
import HomePage from './pages/HomePage.tsx'
import { AuthProvider } from './auth/AuthContext.tsx'

import './App.css'


export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/signup" element={<SignUpPage />} /> 
          <Route path="/login" element={<LoginPage />} />
          <Route path= "/home" element={<HomePage />} /> 
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
