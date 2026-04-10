import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { error } = await signIn({ email, password })
      if (error) throw error
      toast.success('Access Granted.')
      navigate('/dashboard')
    } catch (error) {
      toast.error(error.message || 'Login failed')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 text-on-background">
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel max-w-md w-full p-8 space-y-6 rounded-xl border border-cyan-500/30 shadow-[0_0_40px_rgba(0,242,255,0.1)] relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent pointer-events-none"></div>
        <div className="text-center space-y-3 relative z-10">
          <motion.div 
            whileHover={{ scale: 1.05 }}
            className="mx-auto w-16 h-16 bg-surface-container-highest rounded-xl flex items-center justify-center border border-primary/30 shadow shadow-cyan-500/50"
          >
            <span className="material-symbols-outlined text-cyan-400 text-3xl">terminal</span>
          </motion.div>
          <h1 className="text-2xl font-black font-['Space_Grotesk'] tracking-widest text-cyan-400 uppercase drop-shadow-[0_0_8px_rgba(0,242,255,0.4)]">
            RegulaIntel
          </h1>
          <p className="text-slate-400 text-[10px] font-['Space_Grotesk'] uppercase tracking-widest font-bold border-b border-cyan-500/20 pb-4 inline-block">
            Secure Authentication Protocol
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
          <div>
            <label className="block text-[10px] font-bold font-['Space_Grotesk'] uppercase tracking-widest text-cyan-300 mb-2">
              Officer Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-cyan-500/50 w-4 h-4" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-cyan-500/20 rounded-lg bg-surface-container-lowest text-cyan-50 focus:ring-1 focus:ring-cyan-400 focus:border-cyan-400 transition-all font-mono text-sm placeholder-slate-600"
                placeholder="system.admin@regulaintel.io"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-bold font-['Space_Grotesk'] uppercase tracking-widest text-cyan-300 mb-2">
              Authorization Key
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-cyan-500/50 w-4 h-4" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-10 py-3 border border-cyan-500/20 rounded-lg bg-surface-container-lowest text-cyan-50 focus:ring-1 focus:ring-cyan-400 focus:border-cyan-400 transition-all font-mono text-sm placeholder-slate-600"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-cyan-500/50 hover:text-cyan-400 transition-colors"
                tabIndex="-1"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full bg-cyan-500/10 border border-cyan-400 text-cyan-400 font-bold py-3 px-4 rounded-lg shadow-[0_0_15px_rgba(0,242,255,0.2)] hover:bg-cyan-500/20 hover:shadow-[0_0_20px_rgba(0,242,255,0.4)] transition-all font-['Space_Grotesk'] text-[12px] uppercase tracking-widest disabled:opacity-50 flex justify-center items-center gap-2 mt-4"
          >
            {loading ? (
              <>
                <span className="material-symbols-outlined animate-spin text-sm">sync</span>
                Authenticating...
              </>
            ) : (
              'Initialize Session'
            )}
          </motion.button>

          <div className="text-center pt-2">
            <p className="text-[10px] font-['Space_Grotesk'] text-slate-500 uppercase tracking-widest">
              No access clearance?{' '}
              <Link to="/register" className="font-bold text-cyan-500 hover:text-cyan-300 transition-colors border-b border-transparent hover:border-cyan-300 pb-0.5 ml-1">
                Request Auth
              </Link>
            </p>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

export default Login
