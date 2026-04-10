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
    <div className="min-h-screen flex items-center justify-center p-4 bg-zinc-950 text-zinc-50 relative selection:bg-indigo-500/30">
      {/* Soft background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none opacity-50"></div>
      
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full p-10 space-y-8 rounded-2xl border border-zinc-800 bg-zinc-900/60 backdrop-blur-xl shadow-2xl relative overflow-hidden"
      >
        <div className="text-center space-y-4 relative z-10">
          <motion.div 
            whileHover={{ scale: 1.05 }}
            className="mx-auto w-14 h-14 bg-zinc-800 rounded-xl flex items-center justify-center shadow-inner border border-zinc-700"
          >
            <span className="material-symbols-outlined text-zinc-100 text-2xl">terminal</span>
          </motion.div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white mb-1">
              RegulaIntel Auth
            </h1>
            <p className="text-zinc-400 text-sm font-medium">
              Secure System Authentication Protocol
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2 px-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500 w-4 h-4" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-11 pr-4 py-3 border border-zinc-700 rounded-xl bg-zinc-900 text-zinc-100 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm placeholder-zinc-600 outline-none"
                placeholder="system.admin@regulaintel.io"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2 px-1">
              Authorization Key
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500 w-4 h-4" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-11 pr-11 py-3 border border-zinc-700 rounded-xl bg-zinc-900 text-zinc-100 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm placeholder-zinc-600 outline-none"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                tabIndex="-1"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className={`w-full py-3.5 px-4 mt-8 rounded-xl font-bold text-[12px] uppercase tracking-wider transition-all flex justify-center items-center gap-2 ${loading ? 'bg-zinc-800 text-zinc-500' : 'bg-white text-zinc-950 hover:bg-zinc-200 shadow-[0_0_20px_rgba(255,255,255,0.1)]'}`}
          >
            {loading ? (
              <>
                <span className="material-symbols-outlined animate-spin text-[16px]">sync</span>
                Authenticating...
              </>
            ) : (
              'Initialize Session'
            )}
          </motion.button>

          <div className="text-center pt-5 border-t border-zinc-800 mt-6">
            <p className="text-sm font-medium text-zinc-500">
              No access clearance?{' '}
              <Link to="/register" className="font-semibold text-white hover:text-indigo-400 transition-colors">
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
