import { useEffect, useState } from 'react'
import './App.css'

const TOKEN_KEY = 'my-dictionary-refresh'

async function post(path, body) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = response.status !== 204 && response.headers.get('content-type')?.includes('application/json')
    ? await response.json()
    : null
  if (!response.ok) {
    const messages = data && Object.values(data).flat().filter((value) => typeof value === 'string')
    const error = new Error(messages?.join(' ') || `Request failed (${response.status}).`)
    error.status = response.status
    throw error
  }
  return data
}

function Words() {
  const [words, setWords] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/words/', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Request failed: ${response.status}`)
        return response.json()
      })
      .then((data) => setWords(data.words))
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message)
      })
    return () => controller.abort()
  }, [])

  return (
    <section>
      <h2>Sample words</h2>
      {error && <p role="alert">Could not load words: {error}</p>}
      {!error && words === null && <p>Loading...</p>}
      {words && <ul>{words.map((word) => <li key={word}>{word}</li>)}</ul>}
    </section>
  )
}

function App() {
  const [screen, setScreen] = useState(() => localStorage.getItem(TOKEN_KEY) ? 'restoring' : 'signin')
  const [sessionToken, setSessionToken] = useState(null)
  const [retry, setRetry] = useState(0)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) return
    let active = true
    post('/api/auth/refresh/', { refresh: token })
      .then(() => {
        if (active) {
          setSessionToken(token)
          setScreen('signedin')
        }
      })
      .catch((err) => {
        if (!active) return
        if (err.status === 401) {
          if (localStorage.getItem(TOKEN_KEY) === token) localStorage.removeItem(TOKEN_KEY)
          setMessage('Your session expired. Please sign in again.')
          setScreen('signin')
        } else {
          setError(`Could not restore your session: ${err.message}`)
          setScreen('restore-error')
        }
      })
    return () => { active = false }
  }, [retry])

  function navigate(next) {
    setError('')
    setMessage('')
    setPassword('')
    setConfirmation('')
    setScreen(next)
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    if (screen === 'signup' && password !== confirmation) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    try {
      if (screen === 'signup') {
        await post('/api/auth/signup/', { email, password })
        setPassword('')
        setConfirmation('')
        setMessage('Account created. Please sign in.')
        setScreen('signin')
      } else {
        const data = await post('/api/auth/signin/', { email, password })
        localStorage.setItem(TOKEN_KEY, data.refresh)
        setSessionToken(data.refresh)
        setPassword('')
        setScreen('signedin')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function signout() {
    setError('')
    setBusy(true)
    try {
      await post('/api/auth/signout/', { refresh: sessionToken })
      if (localStorage.getItem(TOKEN_KEY) === sessionToken) localStorage.removeItem(TOKEN_KEY)
      setSessionToken(null)
      setScreen('signedout')
    } catch (err) {
      if (err.status === 401) {
        if (localStorage.getItem(TOKEN_KEY) === sessionToken) localStorage.removeItem(TOKEN_KEY)
        setSessionToken(null)
        setMessage('Your session expired. Please sign in again.')
        setScreen('signin')
      } else {
        setError(`Could not sign out: ${err.message}`)
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <main>
      <h1>My Dictionary</h1>
      <section aria-label="Authentication">
        {screen === 'restoring' && <p>Restoring your session...</p>}
        {screen === 'restore-error' && (
          <button type="button" onClick={() => { setError(''); setScreen('restoring'); setRetry((value) => value + 1) }}>
            Retry
          </button>
        )}
        {(screen === 'signin' || screen === 'signup') && (
          <>
            <h2>{screen === 'signin' ? 'Sign in' : 'Sign up'}</h2>
            <form onSubmit={submit}>
              <label>Email <input type="email" autoComplete="email" required maxLength={150} value={email} onChange={(event) => setEmail(event.target.value)} /></label>
              <label>Password <input type="password" autoComplete={screen === 'signin' ? 'current-password' : 'new-password'} required maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
              {screen === 'signup' && (
                <label>Confirm password <input type="password" autoComplete="new-password" required maxLength={128} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></label>
              )}
              <button disabled={busy}>{busy ? 'Please wait...' : screen === 'signin' ? 'Sign in' : 'Sign up'}</button>
            </form>
            <button type="button" className="link" disabled={busy} onClick={() => navigate(screen === 'signin' ? 'signup' : 'signin')}>
              {screen === 'signin' ? 'Create an account' : 'Already have an account? Sign in'}
            </button>
          </>
        )}
        {screen === 'signedin' && (
          <>
            <h2>Signed in</h2>
            <button type="button" onClick={() => navigate('signout')}>Sign out</button>
          </>
        )}
        {screen === 'signout' && (
          <>
            <h2>Sign out</h2>
            <p>Are you sure you want to sign out?</p>
            <button type="button" disabled={busy} onClick={signout}>{busy ? 'Signing out...' : 'Confirm sign out'}</button>
            <button type="button" className="link" disabled={busy} onClick={() => navigate('signedin')}>Cancel</button>
          </>
        )}
        {screen === 'signedout' && (
          <>
            <h2>Signed out</h2>
            <button type="button" onClick={() => navigate('signin')}>Sign in</button>
          </>
        )}
        {message && <p role="status">{message}</p>}
        {error && <p role="alert">{error}</p>}
      </section>
      <Words />
    </main>
  )
}

export default App
