// Imports
import { useState } from 'react'

// Declaration of Types
type SignUpField = 'username' | 'email' | 'password'
type FormErrors = Partial<Record<SignUpField | 'form', string>>

// Declaration of Interfaces
interface SignUpResponse {
    id: number
    username: string
    email: string
    created_at: string
    }

// Error Validation Function
function validateSignUpForm(username: string, email: string, password: string): FormErrors {
    let errors: FormErrors = {}

    // Username Validation
    const trimmedUsername = username.trim()
    if (!trimmedUsername) {
        errors.username = 'Username is required.'
    } else if (trimmedUsername.length < 3) {
        errors.username = 'Username must be at least 3 characters long.'
    } else if (trimmedUsername.length > 50) {
        errors.username = 'Username must be less than 50 characters long.'
    }
    // Email Validation
    const trimmedEmail = email.trim()
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/

    if (!trimmedEmail) {
        errors.email = 'Email is required.'
    } else if (!emailRegex.test(trimmedEmail)) {
        errors.email = 'Please enter a valid email address.'
    }

    // Password Validation
    if (!password) {
        errors.password = 'Password is required.'
    } else if (password.length < 6) {
        errors.password = 'Password must be at least 6 characters long.'
    } else if (password.length > 70) {
        errors.password = 'Password must be less than 70 characters long.'
    } else if (!/[A-Z]/.test(password)){
        errors.password = 'Password must contain at least one uppercase letter.'
    } else if (!/[a-z]/.test(password)){
        errors.password = 'Password must contain at least one lowercase letter.'
    } else if (!/[0-9]/.test(password)){
        errors.password = 'Password must contain at least one number.'
    }

    return errors
}

// Narrows a backend field name (any string) down to one of our form fields
function isSignUpField(value: unknown): value is SignUpField {
    return value === 'username' || value === 'email' || value === 'password'
}


// Sign Function
export default function SignUpPage() {
    // Set consts
    const [email, setEmail] = useState('')
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState<FormErrors>({})

    const handleSignUp = async (e : React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        // Client-side Validiation for empty fields using the validateSignUpForm function
        const validationErrors = validateSignUpForm(username, email, password);
        setError(validationErrors)

        if (Object.keys(validationErrors).length > 0) {
            return; // Stop submission if there are validation errors
        }

        try {
            let response = await fetch('http://localhost:8000/sign-up', {
                method : 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
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

                        if (isSignUpField(field) && !serverErrors[field]) {
                            serverErrors[field] = message
                        } else if (!isSignUpField(field) && !serverErrors.form) {
                            // An error not tied to one of our inputs (e.g. a malformed body)
                            serverErrors.form = message
                        }
                    }

                    setError(serverErrors)
                } else if (response.status === 400) {
                    // HTTPException: detail is a plain string
                    if (body.detail === 'Email already taken.') {
                        setError({ email: body.detail })
                    } else if (body.detail === 'Username already taken.') {
                        setError({ username: body.detail })
                    } else {
                        setError({ form: body.detail ?? 'Sign up failed.' })
                    }
                } else {
                    setError({ form: 'Something went wrong. Please try again.' })
                }
                return
            }

            const data: SignUpResponse = await response.json()
            console.log('Sign up successful:', data)

        } catch {
            // fetch() itself throws when the server can't be reached (backend down, CORS, no network)
            setError({ form: 'Could not reach the server. Please try again later.' })
        }
    }


return (
    <div>
        <header>
            <h1>Sign Up</h1>
        </header>

        <form onSubmit={handleSignUp} noValidate>
            <input
                type="text"
                value={username}
                placeholder="Username"
                onChange={(e) => setUsername(e.target.value)}
                required
                aria-invalid={!!error.username}
            />
            {error.username && <p className="field-error">{error.username}</p>}
            <input
                type="email"
                value={email}
                placeholder="Email"
                onChange={(e) => setEmail(e.target.value)}
                required
                aria-invalid={!!error.email}
            />
            {error.email && <p className="field-error">{error.email}</p>}
            <input
                type="password"
                value={password}
                placeholder="Password"
                onChange={(e) => setPassword(e.target.value)}
                required
                aria-invalid={!!error.password}
            />
            {error.password && <p className="field-error">{error.password}</p>}
            <button type="submit">Sign Up</button>
            {error && <p style={{ color: 'red' }}></p>}
        </form>
    </div>
    )
}