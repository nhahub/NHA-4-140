'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, Sparkles } from 'lucide-react'
import { useCompareStore } from '@/store/compareStore'
import CarScanner from './CarScanner'
import AnalysisTimeline from './AnalysisTimeline'
import ThinkingPanel from './ThinkingPanel'
import ProgressCard from './ProgressCard'
import AnimatedMetric from './AnimatedMetric'

interface Props {
  isLoading: boolean
  statusText: string
  progress: { current: number; total: number }
  onCancel?: () => void
}

export default function AIComparisonLoading({ isLoading, statusText, progress, onCancel }: Props) {
  const { ads } = useCompareStore()

  if (!isLoading) return null

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 overflow-y-auto"
        style={{ background: 'radial-gradient(ellipse at top, rgba(15,15,35,1) 0%, rgba(5,5,15,1) 100%)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0, transition: { duration: 0.6 } }}
      >
        <div className="relative z-10 min-h-screen px-4 py-6">
          {/* Header */}
          <div className="flex items-center justify-between max-w-5xl mx-auto mb-8">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-widest">
                AI Comparison Engine
              </span>
            </div>
            {onCancel && (
              <button
                onClick={onCancel}
                className="text-white/30 hover:text-white/60 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Car Scanners */}
          <div className="max-w-3xl mx-auto mb-10">
            <div className="grid grid-cols-2 gap-4 md:gap-8">
              {ads.slice(0, 2).map((ad, i) => (
                <CarScanner
                  key={ad.id}
                  brand={ad.brand}
                  model={ad.model}
                  imageUrl={ad.cover_image_url}
                  index={i}
                />
              ))}
            </div>

            {/* VS Badge */}
            <motion.div
              className="flex justify-center -mt-5 mb-4"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.4, type: 'spring', stiffness: 300 }}
            >
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold tracking-wider border"
                style={{
                  background: 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.2))',
                  borderColor: 'rgba(59,130,246,0.3)',
                  color: 'rgba(147,197,253,0.9)',
                }}
              >
                VS
              </div>
            </motion.div>
          </div>

          {/* Analysis Content */}
          <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left: Progress Cards & Metrics */}
            <div className="space-y-4">
              {progress.total > 0 && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <ProgressCard
                      title="Analysis Stage"
                      value={`${progress.current} of ${progress.total} complete`}
                      color="#3b82f6"
                      delay={0.2}
                    />
                  </div>
                  <ProgressCard
                    title="Exterior"
                    value="Inspected"
                    color="#10b981"
                    delay={0.3}
                  />
                  <ProgressCard
                    title="Market Data"
                    value="Analyzed"
                    color="#8b5cf6"
                    delay={0.4}
                  />
                </div>
              )}

              <AnimatedMetric
                label="Analysis Progress"
                value={progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0}
                suffix="%"
                color="#3b82f6"
                delay={300}
              />

              <ThinkingPanel statusText={statusText} />
            </div>

            {/* Right: Analysis Timeline */}
            <div>
              <div
                className="rounded-xl border border-white/5 p-4 h-full"
                style={{ background: 'rgba(15,15,25,0.6)', backdropFilter: 'blur(12px)' }}
              >
                <p className="text-[10px] uppercase tracking-widest font-semibold text-white/30 mb-3">
                  Live Analysis Log
                </p>
                <AnalysisTimeline progress={progress} />
              </div>
            </div>
          </div>

          {/* Status Bar */}
          <motion.div
            className="fixed bottom-0 left-0 right-0 z-20"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div
              className="max-w-5xl mx-auto px-4 py-2 flex items-center gap-3 text-xs"
              style={{ background: 'rgba(10,10,25,0.8)', backdropFilter: 'blur(12px)', borderTop: '1px solid rgba(255,255,255,0.05)' }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              <span className="text-white/50">{statusText || 'Initializing AI analysis...'}</span>
              <span className="ml-auto text-white/20 font-mono">
                {progress.total > 0 ? `${progress.current}/${progress.total}` : ''}
              </span>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
