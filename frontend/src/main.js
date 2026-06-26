import './style.css'

const API_URL = 'http://localhost:8000'

const params = new URLSearchParams(window.location.search)
const githubToken = params.get('github_token')

if (githubToken) {
  window.history.replaceState({}, '', '/')

  document.querySelector('#app').innerHTML = `
    <div class="card">
      <h1>PR Conductor</h1>
      <p class="subtitle">GitHub connected. Now add your Gemini API key.</p>

      <form id="register-form">
        <label for="gemini-key">Gemini API Key</label>
        <input type="password" id="gemini-key" placeholder="AIzaxxxxxxxxxx" required />

        <button type="submit">Register</button>
      </form>

      <p class="error" id="error"></p>

      <div class="result" id="result">
        <h3>Setup Complete</h3>

        <div class="setup-steps">
          <div class="step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h4>Copy your secret key</h4>
              <div class="secret-key-wrapper">
                <div class="secret-key" id="secret-key"></div>
                <button type="button" class="copy-btn" id="copy-btn">Copy</button>
              </div>
            </div>
          </div>

          <div class="step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h4>Add it to your GitHub repo</h4>
              <p class="step-detail">Go to your repo on GitHub:</p>
              <div class="nav-path">
                <span class="nav-item">Settings</span>
                <span class="nav-arrow">&rarr;</span>
                <span class="nav-item">Secrets and variables</span>
                <span class="nav-arrow">&rarr;</span>
                <span class="nav-item">Actions</span>
                <span class="nav-arrow">&rarr;</span>
                <span class="nav-item highlight">New repository secret</span>
              </div>
              <p class="step-detail">Name: <code>PR_CONDUCTOR_SECRET</code></p>
              <p class="step-detail">Value: paste the key from step 1</p>
            </div>
          </div>

          <div class="step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h4>Add the workflow to your repo</h4>
              <p class="step-detail">Run this in your project folder:</p>
              <div class="command-box">npx pr-conductor</div>
            </div>
          </div>

          <div class="step">
            <div class="step-number">4</div>
            <div class="step-content">
              <h4>You're all set!</h4>
              <p class="step-detail">Open a PR and get automated reviews.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `

  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault()

    const btn = e.target.querySelector('button')
    const errorEl = document.getElementById('error')
    const resultEl = document.getElementById('result')

    btn.disabled = true
    btn.textContent = 'Registering...'
    errorEl.classList.remove('show')
    resultEl.classList.remove('show')

    const geminiKey = document.getElementById('gemini-key').value.trim()

    try {
      const res = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          gemini_key: geminiKey
        })
      })

      if (!res.ok) throw new Error('Registration failed')

      const data = await res.json()

      document.getElementById('secret-key').textContent = data.secret_key
      resultEl.classList.add('show')

      document.getElementById('copy-btn').addEventListener('click', () => {
        navigator.clipboard.writeText(data.secret_key)
        document.getElementById('copy-btn').textContent = 'Copied!'
        setTimeout(() => document.getElementById('copy-btn').textContent = 'Copy', 2000)
      })
    } catch (err) {
      errorEl.textContent = err.message
      errorEl.classList.add('show')
    } finally {
      btn.disabled = false
      btn.textContent = 'Register'
    }
  })

} else {
  document.querySelector('#app').innerHTML = `
    <div class="card">
      <h1>PR Conductor</h1>
      <p class="subtitle">Set up automated PR reviews for your repos</p>

      <a href="${API_URL}/auth/github" class="github-btn">Login with GitHub</a>
    </div>
  `
}
