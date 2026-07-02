'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Box {
  id: number
  x: number
  y: number
  width: number
  height: number
  label: string
  confidence: number
}

const LABELS = [
  'Front Bumper', 'Hood', 'Windshield', 'Roof',
  'Driver Door', 'Rear Door', 'Rear Bumper', 'Trunk',
  'Front Left Tire', 'Front Right Tire', 'Rear Left Tire', 'Rear Right Tire',
  'Headlight', 'Taillight', 'Side Mirror', 'Fender',
]

function randomBetween(min: number, max: number) {
  return Math.random() * (max - min) + min
}

function generateBox(id: number): Box {
  const w = randomBetween(15, 35)
  const h = randomBetween(10, 25)
  return {
    id,
    x: randomBetween(2, 78),
    y: randomBetween(5, 75),
    width: w,
    height: h,
    label: LABELS[Math.floor(Math.random() * LABELS.length)],
    confidence: Math.floor(randomBetween(82, 99)),
  }
}

export default function DetectionBoxes() {
  const [boxes, setBoxes] = useState<Box[]>([])

  useEffect(() => {
    const initial = Array.from({ length: 5 }, (_, i) => generateBox(i))
    setBoxes(initial)

    const interval = setInterval(() => {
      setBoxes((prev) => {
        const keep = prev.filter(() => Math.random() > 0.4)
        if (keep.length < 2) {
          keep.push(generateBox(Date.now()))
        }
        if (Math.random() > 0.5) {
          keep.push(generateBox(Date.now()))
        }
        return keep.slice(-6)
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="absolute inset-0 pointer-events-none">
      <AnimatePresence>
        {boxes.map((box) => (
          <motion.div
            key={box.id}
            className="absolute"
            style={{
              left: `${box.x}%`,
              top: `${box.y}%`,
              width: `${box.width}%`,
              height: `${box.height}%`,
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          >
            <div
              className="w-full h-full rounded-sm border"
              style={{
                borderColor: 'rgba(59, 130, 246, 0.6)',
                boxShadow: 'inset 0 0 15px rgba(59, 130, 246, 0.15), 0 0 10px rgba(59, 130, 246, 0.1)',
              }}
            />
            <div
              className="absolute -top-5 left-0 text-[9px] font-mono whitespace-nowrap px-1 py-0.5 rounded"
              style={{
                background: 'rgba(59, 130, 246, 0.2)',
                color: 'rgba(147, 197, 253, 0.9)',
                backdropFilter: 'blur(4px)',
              }}
            >
              {box.label} {box.confidence}%
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
