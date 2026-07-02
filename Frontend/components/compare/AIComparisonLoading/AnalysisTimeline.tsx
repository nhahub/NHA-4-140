'use client'

import { motion } from 'framer-motion'
import { CheckCircle2, Loader2, Circle } from 'lucide-react'

interface TimelineStep {
  label: string
  status: 'done' | 'current' | 'pending'
}

const DEFAULT_STEPS: TimelineStep[] = [
  { label: 'Reading advertisement', status: 'pending' },
  { label: 'Extracting specifications', status: 'pending' },
  { label: 'Inspecting exterior', status: 'pending' },
  { label: 'Inspecting interior', status: 'pending' },
  { label: 'Researching Egyptian market', status: 'pending' },
  { label: 'Comparing market prices', status: 'pending' },
  { label: 'Estimating maintenance', status: 'pending' },
  { label: 'Running AI reasoning', status: 'pending' },
  { label: 'Generating recommendation', status: 'pending' },
]

export default function AnalysisTimeline({ progress }: { progress: { current: number; total: number } }) {
  const steps = DEFAULT_STEPS.map((step, i) => {
    const idx = i + 1
    if (idx <= progress.current) return { ...step, status: 'done' as const }
    if (idx === progress.current + 1) return { ...step, status: 'current' as const }
    return step
  })

  return (
    <div className="space-y-1">
      {steps.map((step, i) => (
        <motion.div
          key={step.label}
          className="flex items-center gap-2.5 text-xs"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08, duration: 0.3 }}
        >
          {step.status === 'done' ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
          ) : step.status === 'current' ? (
            <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin flex-shrink-0" />
          ) : (
            <Circle className="w-3.5 h-3.5 text-white/10 flex-shrink-0" />
          )}
          <span
            className={
              step.status === 'done'
                ? 'text-emerald-300/80'
                : step.status === 'current'
                  ? 'text-blue-300 font-medium'
                  : 'text-white/20'
            }
          >
            {step.label}
          </span>
        </motion.div>
      ))}
    </div>
  )
}
