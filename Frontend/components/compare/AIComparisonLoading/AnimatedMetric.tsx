'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface Props {
  label: string
  value: number
  max?: number
  suffix?: string
  color?: string
  delay?: number
}

export default function AnimatedMetric({ label, value, max = 100, suffix = '', color = '#3b82f6', delay = 0 }: Props) {
  const [displayed, setDisplayed] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => {
      const duration = 1500
      const start = performance.now()
      const animate = (now: number) => {
        const elapsed = now - start
        const progress = Math.min(elapsed / duration, 1)
        const eased = 1 - Math.pow(1 - progress, 3)
        setDisplayed(Math.round(eased * value))
        if (progress < 1) requestAnimationFrame(animate)
      }
      requestAnimationFrame(animate)
    }, delay)

    return () => clearTimeout(timer)
  }, [value, delay])

  return (
    <motion.div
      className="flex flex-col items-center"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay / 1000, duration: 0.5 }}
    >
      <span className="text-xs text-text-muted mb-1 font-medium">{label}</span>
      <div className="flex items-baseline gap-0.5">
        <span
          className="text-2xl font-bold tabular-nums"
          style={{ color }}
        >
          {displayed}
        </span>
        {suffix && <span className="text-sm text-text-muted">{suffix}</span>}
      </div>
      {max > 0 && (
        <div className="w-full max-w-[100px] h-1 bg-surface-secondary rounded-full mt-1 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: color }}
            initial={{ width: 0 }}
            animate={{ width: `${(value / max) * 100}%` }}
            transition={{ duration: 1.5, delay: delay / 1000, ease: 'easeOut' }}
          />
        </div>
      )}
    </motion.div>
  )
}
