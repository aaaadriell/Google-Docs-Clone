// Imports
import { useState } from 'react'

// Login Function
export default function SignUpPage() {
    // Set consts
    const [email, setEmail] = useState('')
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')

    interface SignUpResponse {
        email: string;
        message: string;
    }

    const handleSignUp = async (e : React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError('');

        // Client-side Validiation for empty fields
        if (!email || !username || !password) {
        setError('Please fill in all fields.');
        return;
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
                throw new Error('Sign up failed');
            }

            let data : SignUpResponse = await response.json();
            console.log('Sign up successful:', data);
        } catch (error : any) {
            setError(error.message);
        }
    }


return (
    <div>
        <header>
            <h1>Sign Up</h1>
        </header>

        <form onSubmit={handleSignUp}>
            <input
                type="username"
                value={username}
                placeholder="Username"
                onChange={(e) => setUsername(e.target.value)}
                required
            />
            <input
                type="email"
                value={email}
                placeholder="Email"
                onChange={(e) => setEmail(e.target.value)}
                required
            />
            <input
                type="password"
                value={password}
                placeholder="Password"
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            <button type="submit">Sign Up</button>
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </form>
    </div>
    )
}