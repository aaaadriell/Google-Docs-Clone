// Imports
import { useState } from 'react'

// Declaration of Types
type LoginField = 'emailOrUsername' | 'password'
type FormErrors = Partial<Record<LoginField | 'form', string>>

// Declaration of Interfaces
interface LoginResponse {
    id: number
    emailOrUsername : string
    jwtToken: string
    refreshToken: string
    }

    // Error Validation Function
function validateLoginForm(emailorUsername: string, password: string): FormErrors {
    let errors: FormErrors = {}

    // Email / Username Validation
    const trimmedEmailorUsername = emailorUsername.trim()
    if (!trimmedEmailorUsername) {
        errors.emailOrUsername = 'Email or Username is required.'
    } else if (trimmedEmailorUsername.length < 3) {
        errors.emailOrUsername = 'Email or Username must be at least 3 characters long.'
    } else if (trimmedEmailorUsername.length > 50) {
        errors.emailOrUsername = 'Email or Username must be less than 50 characters long.'
    }

    // Password Validation
    if (!password) {
        errors.password = 'Password is required.'
    }
    
    return errors
}

function isLoginField(value: unknown): value is LoginField {
    return value === 'emailOrUsername' || value === 'password'
}

// Sign Function
export default function LoginPage() {
    // Set consts
    const [emailOrUsername, setEmailOrUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState<FormErrors>({})

    const handleSignUp = async (e : React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        const validationErrors = validateLoginForm(emailOrUsername, password);
        setError(validationErrors);

        if (Object.keys(validationErrors).length > 0) {
            return; // Stop submission if there are validation errors
        }

        try {
            let response = await fetch('http://localhost:8000/login', {
                method : 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    emailOrUsername,
                    password
                })
            });

            if (!response.ok) {
                const body = await response.json()

                if (response.status === 422) {
                    // Pydantic validation error: detail is an array, one entry per failed field
                    const serverErrors: FormErrors = {}

                    for (const item of body.detail) {
                        const field = item.loc[item.loc.length - 1]  // e.g. ["body", "password"] -> "password"
                        const message = item.msg.replace(/^Value error, /, '')

                        if (isLoginField(field) && !serverErrors[field]) {
                            serverErrors[field] = message
                        } else if (!isLoginField(field) && !serverErrors.form) {
                            // An error not tied to one of our inputs (e.g. a malformed body)
                            serverErrors.form = message
                        }
                    }
                    setError(serverErrors)

                } else if (response.status === 401) {
                    // HTTPException: detail is a plain string
                    if (body.detail === 'Invalid credentials.') {
                        setError({ emailOrUsername: body.detail })
                    } else {
                        setError({ form: body.detail ?? 'Login failed.' })
                    }
                } else {
                    setError({ form: 'Something went wrong. Please try again.' })
                }
                return
            }

            const data: LoginResponse = await response.json()
            console.log('Login successful:', data)

        } catch {
            // fetch() itself throws when the server can't be reached (backend down, CORS, no network)
            setError({ form: 'Could not reach the server. Please try again later.' })
        }
    }


return (
    <div>
        <header>
            <h1>Login</h1>
        </header>

        <form onSubmit={handleSignUp} noValidate>
            <input
                type="text"
                value={emailOrUsername}
                placeholder="Enter Email or Username"
                onChange={(e) => setEmailOrUsername(e.target.value)}
                required
                aria-invalid={!!error.emailOrUsername}
            />
            {error.emailOrUsername && <p className="field-error">{error.emailOrUsername}</p>}
            
            <input
                type="password"
                value={password}
                placeholder="Password"
                onChange={(e) => setPassword(e.target.value)}
                required
                aria-invalid={!!error.password}
            />
            {error.password && <p className="field-error">{error.password}</p>}
            <button type="submit">Login</button>
            {error && <p style={{ color: 'red' }}></p>}
        </form>
    </div>
    )
}