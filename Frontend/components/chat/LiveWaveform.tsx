'use client'

import { useMemo } from 'react'

interface LiveWaveformProps {
  amplitude: number
  barCount?: number
  className?: string
}

const BAR_WIDTH = 3
const BAR_GAP = 2
const MAX_HEIGHT = 32

const SHAPE_CACHE: Record<number, number[]> = {}

function getShape(barCount: number): number[] {
  if (SHAPE_CACHE[barCount]) return SHAPE_CACHE[barCount]
  const shape = Array.from({ length: barCount }, (_, i) => {
    const position = (i / (barCount - 1)) * 2 - 1
    return Math.exp(-(position * position) * 2.5)
  })
  SHAPE_CACHE[barCount] = shape
  return shape
}

export function LiveWaveform({
  amplitude,
  barCount = 40,
  className,
}: LiveWaveformProps) {
  const shape = useMemo(() => getShape(barCount), [barCount])

  return (
    <div
      className={`flex items-center ${className || ''}`}
      style={{
        gap: `${BAR_GAP}px`,
        height: `${MAX_HEIGHT}px`,
      }}
    >
      {shape.map((barFactor, i) => {
        const height = Math.max(2, barFactor * (1 + amplitude * 4) * (MAX_HEIGHT * 0.45))

        return (
          <div
            key={i}
            className="bg-primary-500/80 rounded-full"
            style={{
              width: `${BAR_WIDTH}px`,
              height: `${height}px`,
              transition: 'height 60ms ease-out',
            }}
          />
        )
      })}
    </div>
  )
}
