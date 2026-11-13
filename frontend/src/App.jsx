import { useEffect, useState } from 'react'
import './App.css'

function App() {
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
    <main>
      <h1>My Dictionary</h1>
      <p>Words from the Django backend:</p>
      {error && <p role="alert">Could not load words: {error}</p>}
      {!error && words === null && <p>Loading...</p>}
      {words && (
        <ul>
          {words.map((word) => <li key={word}>{word}</li>)}
        </ul>
      )}
    </main>
  )
}

export default App
