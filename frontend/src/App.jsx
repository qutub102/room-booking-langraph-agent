import { useState, useRef, useEffect } from 'react'
import './App.css'
// Use /api in production (Docker Nginx proxy), and localhost:8000 in local dev
const API_BASE = 'https://room-booking-langraph-agent.onrender.com'

/** Convert basic markdown (bold, newlines) to HTML */
function formatMessage(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

/* ─── Auth Page ──────────────────────────────────────────────── */
function AuthPage({ onLogin }) {
  const [isSignup, setIsSignup] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const url = isSignup ? `${API_BASE}/signup` : `${API_BASE}/login`
    const body = isSignup
      ? { name, email, password }
      : { email, password }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Authentication failed')
      }

      const data = await response.json()
      localStorage.setItem('token', data.token)
      localStorage.setItem('userName', data.name)
      onLogin(data.name, data.token)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-logo">🤖</div>
        <h1 className="auth-title">Room Booking Agent</h1>
        <p className="auth-subtitle">
          {isSignup ? 'Create your account' : 'Welcome back'}
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {isSignup && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                required
              />
            </div>
          )}
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={4}
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Please wait...' : isSignup ? 'Sign Up' : 'Log In'}
          </button>
        </form>

        <p className="auth-switch">
          {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button onClick={() => { setIsSignup(!isSignup); setError('') }}>
            {isSignup ? 'Log In' : 'Sign Up'}
          </button>
        </p>
      </div>
    </div>
  )
}

/* ─── Calendar View ──────────────────────────────────────────── */
const HOUR_START = 8
const HOUR_END = 21
const TOTAL_HOURS = HOUR_END - HOUR_START

function timeToMinutes(timeStr) {
  const [h, m] = timeStr.split(':').map(Number)
  return h * 60 + m
}

function CalendarView({ schedules, date, onClose, onDateChange }) {
  const [fullscreen, setFullscreen] = useState(false)
  const timeLabels = []
  for (let h = HOUR_START; h <= HOUR_END; h++) {
    timeLabels.push(`${String(h).padStart(2, '0')}:00`)
  }

  const getBookingStyle = (booking) => {
    const startMin = timeToMinutes(booking.start_time)
    const endMin = timeToMinutes(booking.end_time)
    const dayStartMin = HOUR_START * 60
    const dayEndMin = HOUR_END * 60
    const totalMin = dayEndMin - dayStartMin

    const clampedStart = Math.max(startMin, dayStartMin)
    const clampedEnd = Math.min(endMin, dayEndMin)

    const leftPct = ((clampedStart - dayStartMin) / totalMin) * 100
    const widthPct = ((clampedEnd - clampedStart) / totalMin) * 100

    return {
      left: `${leftPct}%`,
      width: `${Math.max(widthPct, 0.5)}%`,
    }
  }

  const changeDate = (offset) => {
    const d = new Date(date)
    d.setDate(d.getDate() + offset)
    const newDate = d.toISOString().split('T')[0]
    onDateChange(newDate)
  }

  const calendarContent = (
    <>
      <div className="calendar-header">
        <div className="calendar-nav">
          <button className="nav-btn" onClick={() => changeDate(-1)}>◀</button>
          <h2>📅 {date}</h2>
          <button className="nav-btn" onClick={() => changeDate(1)}>▶</button>
        </div>
        <div className="calendar-actions">
          {!fullscreen && (
            <button className="nav-btn" onClick={() => setFullscreen(true)} title="Fullscreen">⤢</button>
          )}
          {fullscreen && (
            <button className="nav-btn" onClick={() => setFullscreen(false)} title="Exit fullscreen">⤡</button>
          )}
          <button className="close-btn" onClick={() => { setFullscreen(false); onClose() }}>✕</button>
        </div>
      </div>

      <div className="calendar-scroll">
        {/* Time ruler */}
        <div className="timeline-ruler">
          <div className="room-label-space"></div>
          <div className="ruler-track">
            {timeLabels.map(label => (
              <div key={label} className="ruler-tick">
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Room rows */}
        {schedules.map(room => (
          <div key={room.room_id} className="timeline-row">
            <div className="room-label">
              <span className="room-name">{room.room_name}</span>
              <span className="room-cap">{room.capacity} seats</span>
            </div>
            <div className="timeline-track">
              {/* Grid lines */}
              {timeLabels.map((_, i) => (
                <div key={i} className="grid-line" style={{ left: `${(i / TOTAL_HOURS) * 100}%` }} />
              ))}
              {/* Booking bars */}
              {room.bookings.map((booking, i) => (
                <div
                  key={i}
                  className="booking-bar"
                  style={getBookingStyle(booking)}
                  title={`${booking.organizer} — ${booking.start_time} to ${booking.end_time}`}
                >
                  <span className="booking-bar-text">
                    {booking.start_time}–{booking.end_time}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="calendar-legend">
        <span className="legend-item"><span className="legend-dot available"></span> Available</span>
        <span className="legend-item"><span className="legend-dot booked"></span> Booked</span>
      </div>
    </>
  )

  if (fullscreen) {
    return (
      <div className="calendar-fullscreen-backdrop" onClick={() => setFullscreen(false)}>
        <div className="calendar-fullscreen" onClick={(e) => e.stopPropagation()}>
          <div className="calendar-container">
            {calendarContent}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="calendar-overlay">
      <div className="calendar-container">
        {calendarContent}
      </div>
    </div>
  )
}

/* ─── Main Chat App ──────────────────────────────────────────── */
function ChatApp({ userName, onLogout }) {
  const [messages, setMessages] = useState([
    { text: `Hi ${userName}! I'm your Room Booking Agent. How can I help you today?`, isUser: false }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showCalendar, setShowCalendar] = useState(true)
  const [calendarData, setCalendarData] = useState(null)
  const [calendarDate, setCalendarDate] = useState(new Date().toISOString().split('T')[0])
  const messagesEndRef = useRef(null)

  const [sessionId] = useState(() => Math.random().toString(36).substring(2, 10))

  const CALENDAR_KEYWORDS = ['calendar', 'available room', 'show room', 'room availability', 'show me room', 'available rooms']

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const fetchCalendar = async (date) => {
    const d = date || calendarDate
    try {
      const response = await fetch(`${API_BASE}/calendar?date=${d}`)
      if (response.ok) {
        const data = await response.json()
        setCalendarData(data)
      }
    } catch (error) {
      console.error('Failed to load calendar:', error)
    }
  }

  useEffect(() => {
    fetchCalendar(calendarDate)
  }, [calendarDate])

  const handleDateChange = (newDate) => {
    setCalendarDate(newDate)
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!inputValue.trim()) return

    const userMessage = inputValue.trim()
    setInputValue('')

    setMessages(prev => [...prev, { text: userMessage, isUser: true }])
    setIsLoading(true)

    const lowerMsg = userMessage.toLowerCase()
    const wantsCalendar = CALENDAR_KEYWORDS.some(kw => lowerMsg.includes(kw))

    if (wantsCalendar) {
      await fetchCalendar()
      setShowCalendar(true)
    } else {
      setShowCalendar(false)
    }

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
          username: userName
        }),
      })

      if (!response.ok) throw new Error('Network response was not ok')

      const data = await response.json()
      setMessages(prev => [...prev, { text: data.response, isUser: false }])

      // Refresh calendar after booking-related messages
      if (lowerMsg.includes('book') || data.response.toLowerCase().includes('booked')) {
        await fetchCalendar()
      }
    } catch (error) {
      console.error('Error fetching chat response:', error)
      setMessages(prev => [...prev, {
        text: "Sorry, I encountered an error connecting to the server. Please ensure the backend is running.",
        isUser: false
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-container">
      <header className="header">
        <div className="avatar">🤖</div>
        <div className="header-text">
          <h1>Room Booking Agent</h1>
          <p>Welcome, {userName}</p>
        </div>
        <button
          className="calendar-toggle"
          onClick={() => setShowCalendar(!showCalendar)}
          title="Toggle calendar view"
        >
          📅
        </button>
        <button className="logout-btn" onClick={onLogout} title="Log out">
          ↪
        </button>
      </header>

      {showCalendar && calendarData && (
        <CalendarView
          schedules={calendarData.schedules}
          date={calendarData.date}
          onClose={() => setShowCalendar(false)}
          onDateChange={handleDateChange}
        />
      )}

      <div className="chat-area">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.isUser ? 'user' : 'agent'}`}>
            <div className="message" dangerouslySetInnerHTML={{ __html: formatMessage(msg.text) }} />
          </div>
        ))}

        {isLoading && (
          <div className="typing-indicator agent">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-area" onSubmit={handleSendMessage}>
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="E.g., Book a room for 8 people tomorrow..."
            disabled={isLoading}
            autoFocus
          />
          <button
            type="submit"
            className="send-button"
            disabled={!inputValue.trim() || isLoading}
            aria-label="Send message"
          >
            <svg className="send-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  )
}

/* ─── Root App ───────────────────────────────────────────────── */
function App() {
  const [user, setUser] = useState(() => {
    const savedName = localStorage.getItem('userName')
    const savedToken = localStorage.getItem('token')
    return savedName && savedToken ? { name: savedName, token: savedToken } : null
  })

  const handleLogin = (name, token) => {
    setUser({ name, token })
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userName')
    setUser(null)
  }

  if (!user) {
    return <AuthPage onLogin={handleLogin} />
  }

  return <ChatApp userName={user.name} onLogout={handleLogout} />
}

export default App
