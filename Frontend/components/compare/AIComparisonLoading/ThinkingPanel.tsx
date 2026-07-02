'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Loader2 } from 'lucide-react'

const THINKING_STEPS = [
  { label: 'Vehicle specifications', icon: 'check' },
  { label: 'Visual condition analysis', icon: 'check' },
  { label: 'Market reputation', icon: 'check' },
  { label: 'Price fairness evaluation', icon: 'check' },
  { label: 'Searching owner experiences...', icon: 'loading' },
  { label: 'Looking for reliability reports...', icon: 'pending' },
  { label: 'Comparing resale value...', icon: 'pending' },
  { label: 'Generating recommendation...', icon: 'pending' },
]

export default function ThinkingPanel({ statusText }: { statusText: string }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<string[]>([])

  useEffect(() => {
    if (!statusText) return
    setCompletedSteps((prev) => (prev.includes(statusText) ? prev : [...prev, statusText]))
  }, [statusText])

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((c) => Math.min(c + 1, THINKING_STEPS.length - 1))
    }, 2500)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="rounded-xl border border-white/5 p-4" style={{ background: 'rgba(15,15,25,0.6)', backdropFilter: 'blur(12px)' }}>
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-blue-400" />
        <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">AI Reasoning</span>
      </div>
      <div className="space-y-1.5">
        {THINKING_STEPS.map((step, i) => {
          const isActive = i === currentStep
          const isDone = i < currentStep
          return (
            <motion.div
              key={step.label}
              className="flex items-center gap-2 text-xs"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.15, duration: 0.3 }}
            >
              {isDone ? (
                <span className="text-emerald-400 text-[10px]">✓</span>
              ) : isActive ? (
                <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
              ) : (
                <span className="text-white/20 text-[10px]">○</span>
              )}
              <span
                className={
                  isDone
                    ? 'text-emerald-300/80'
                    : isActive
                      ? 'text-blue-300'
                      : 'text-white/30'
                }
              >
                {step.label}
              </span>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
