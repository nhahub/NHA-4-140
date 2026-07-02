'use client'

import Image from 'next/image'
import { motion } from 'framer-motion'
import ScanBeam from './ScanBeam'
import DetectionBoxes from './DetectionBoxes'

interface Props {
  brand: string
  model: string
  imageUrl: string
  index: number
}

function CornerBrackets() {
  const props = 'w-3 h-3 border-blue-400/60'
  return (
    <>
      <div className={`absolute top-1 left-1 border-t-2 border-l-2 ${props}`} />
      <div className={`absolute top-1 right-1 border-t-2 border-r-2 ${props}`} />
      <div className={`absolute bottom-1 left-1 border-b-2 border-l-2 ${props}`} />
      <div className={`absolute bottom-1 right-1 border-b-2 border-r-2 ${props}`} />
    </>
  )
}

export default function CarScanner({ brand, model, imageUrl, index }: Props) {
  return (
    <motion.div
      className="relative flex flex-col items-center"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.2, duration: 0.6, ease: 'easeOut' }}
    >
      <div className="relative w-full aspect-[4/3] rounded-xl overflow-hidden bg-black/60 border border-white/5">
        <Image
          src={imageUrl || '/placeholder.svg'}
          alt={`${brand} ${model}`}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 50vw"
          priority
        />

        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(59,130,246,0.03) 1px, transparent 1px),
              linear-gradient(90deg, rgba(59,130,246,0.03) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px',
          }}
        />

        <ScanBeam />
        <DetectionBoxes />
        <CornerBrackets />

        <div className="absolute bottom-2 left-2">
          <div
            className="text-[9px] font-mono px-1.5 py-0.5 rounded flex items-center gap-1.5"
            style={{
              background: 'rgba(59, 130, 246, 0.15)',
              color: 'rgba(147, 197, 253, 0.9)',
              backdropFilter: 'blur(4px)',
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            AI Vision
          </div>
        </div>
      </div>

      <motion.p
        className="text-xs font-medium text-white/70 mt-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 + index * 0.2 }}
      >
        {brand} {model}
      </motion.p>
    </motion.div>
  )
}
