// Imports
import { useNavigate } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import { useState } from 'react'

// Sign Function
export default function HomePage() {
    // Set consts
    const navigate = useNavigate()
    const { jwtToken, user, logout } = useAuth()
    const [error, setError] = useState<string | null>(null)

    const handleLogout = async () => {
        try{
            let response = await fetch('http://localhost:8000/logout', {
                method: 'POST',
                credentials: 'include', // Include cookies in the request
            })
            if (!response.ok) {
                throw new Error('Logout failed.')
            }
        } catch (error: any) {
            setError(error.message)
        }
        logout() // JWT & Refresh Tokens should be cleared
        navigate('/login', { replace: true })  // Redirect to login page after logout
    }

    return (
        <div>
            <header>
                <h1>HOME PAGE</h1>
            </header>
            <main>
                <p>Welcome, {user?.emailOrUsername}!</p>
                <p>Your JWT Token: {jwtToken}</p>
                <button onClick={handleLogout}>Logout</button>
                {error && <p style={{ color: 'red' }}>{error}</p>}
            </main>
        </div>
    )
}