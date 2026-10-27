// Imports
import { useNavigate } from 'react-router'
import { useAuth } from '../auth/AuthContext'

// Sign Function
export default function HomePage() {
    // Set consts
    const navigate = useNavigate()
    const { jwtToken, user, logout } = useAuth()

    const handleLogout = () => {
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
            </main>
        </div>
    )
}