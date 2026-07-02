'use client'

import { motion } from 'framer-motion'
import { CheckCircle2 } from 'lucide-react'

interface Props {
  title: string
  value: string
  color?: string
  delay?: number
}

export default function ProgressCard({ title, value, color = '#3b82f6', delay = 0 }: Props) {
  return (
    <motion.div
      className="rounded-xl border p-3"
      style={{
        borderColor: `${color}20`,
        background: `linear-gradient(135deg, ${color}08, transparent)`,
      }}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, duration: 0.5, ease: 'easeOut' }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-wider font-semibold" style={{ color: `${color}99` }}>
            {title}
          </p>
          <p className="text-sm font-medium text-white mt-0.5">{value}</p>
        </div>
        <CheckCircle2 className="w-4 h-4" style={{ color }} />
      </div>
    </motion.div>
  )
}
