import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'

// Types
export interface AuthUser {
    id: number
    emailOrUsername: string
}

interface AuthContextValue {
    jwtToken: string | null
    user: AuthUser | null
    login: (token: string, user: AuthUser) => void
    logout: () => void
}

// Creating the Context Object
const AuthContext = createContext<AuthContextValue | null>(null)

// Creating the Provider
export function AuthProvider({ children }: { children: ReactNode }) {
    const [jwtToken, setJwtToken] = useState<string | null>(null)
    const [user, setUser] = useState<AuthUser | null>(null)

    const login = (token: string, user: AuthUser) => {
        setJwtToken(token)
        setUser(user)
    }

    const logout = () => {
        setJwtToken(null)
        setUser(null)
    }

    return (
        <AuthContext value={{ jwtToken, user, login, logout }}>
            {children}
        </AuthContext>
    )
}

// Creating the Hook
export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
