import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAppStore } from '../store/useAppStore'
import { authApi } from '../utils/api'
import toast from 'react-hot-toast'

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAppStore((s) => s.setAuth)
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ email: '', password: '', username: '', full_name: '' })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = mode === 'login'
        ? await authApi.login(form.email, form.password)
        : await authApi.register(form.email, form.username, form.password, form.full_name)
      setAuth(res.data.access_token, res.data.user)
      toast.success('ACCESS GRANTED')
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-nexus-black grid-bg overflow-hidden relative">
      {/* Scanline overlay */}
      <div className="absolute inset-0 scanline pointer-events-none opacity-30" />

      {/* Animated grid corner decorations */}
      <div className="absolute top-4 left-4 w-16 h-16 border-l-2 border-t-2 border-nexus-cyan/50" />
      <div className="absolute top-4 right-4 w-16 h-16 border-r-2 border-t-2 border-nexus-cyan/50" />
      <div className="absolute bottom-4 left-4 w-16 h-16 border-l-2 border-b-2 border-nexus-cyan/50" />
      <div className="absolute bottom-4 right-4 w-16 h-16 border-r-2 border-b-2 border-nexus-cyan/50" />

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 3, repeat: Infinity }}
            className="text-nexus-cyan font-mono text-4xl font-bold tracking-widest text-glow-cyan mb-2"
          >
            NEXUS ATLAS
          </motion.div>
          <div className="text-nexus-muted font-mono text-xs tracking-widest uppercase">
            Geospatial Intelligence Platform
          </div>
          <div className="mt-2 text-nexus-cyan/50 font-mono text-[10px]">
            ◆ CLASSIFIED SYSTEM — AUTHORIZED PERSONNEL ONLY ◆
          </div>
        </div>

        {/* Panel */}
        <div className="nexus-panel nexus-border-glow p-8">
          <div className="flex mb-6 gap-2">
            {(['login', 'register'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 nexus-btn text-xs ${mode === m ? 'nexus-btn-primary' : ''}`}
              >
                {m === 'login' ? 'AUTHENTICATE' : 'NEW OPERATOR'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <>
                <div>
                  <label className="nexus-label">Operator Name</label>
                  <input
                    className="nexus-input"
                    placeholder="callsign"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="nexus-label">Full Name</label>
                  <input
                    className="nexus-input"
                    placeholder="optional"
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  />
                </div>
              </>
            )}
            <div>
              <label className="nexus-label">Email Access Key</label>
              <input
                type="email"
                className="nexus-input"
                placeholder="operator@nexus.mil"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="nexus-label">Security Passphrase</label>
              <input
                type="password"
                className="nexus-input"
                placeholder="••••••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
            </div>
            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full nexus-btn-primary py-3 text-sm tracking-widest"
            >
              {loading ? (
                <span className="animate-pulse">VERIFYING...</span>
              ) : (
                mode === 'login' ? '▶ INITIATE ACCESS' : '▶ CREATE OPERATOR'
              )}
            </motion.button>
          </form>

          <div className="mt-6 pt-4 border-t border-nexus-border">
            <p className="text-nexus-muted font-mono text-[10px] text-center">
              SYSTEM STATUS: ONLINE ◆ NODE: ATLAS-01 ◆ ENCRYPTION: AES-256
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
