'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

export default function ScanBeam({ duration = 3 }: { duration?: number }) {
  const [key, setKey] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => setKey((k) => k + 1), duration * 1000 + 500)
    return () => clearInterval(interval)
  }, [duration])

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <motion.div
        key={key}
        className="absolute left-0 right-0 h-[2px] z-10"
        style={{
          background: 'linear-gradient(90deg, transparent, rgba(59,130,246,0.8), rgba(139,92,246,0.6), transparent)',
          boxShadow: '0 0 20px rgba(59,130,246,0.3), 0 0 60px rgba(59,130,246,0.1)',
        }}
        initial={{ top: 0, opacity: 0 }}
        animate={{
          top: ['0%', '100%'],
          opacity: [0, 1, 1, 0],
        }}
        transition={{
          duration,
          ease: [0.25, 0.1, 0.25, 1],
          times: [0, 0.1, 0.9, 1],
        }}
      />
    </div>
  )
}
