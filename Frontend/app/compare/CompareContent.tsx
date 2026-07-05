'use client'

import Image from 'next/image'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowLeft, Trophy, BarChart3, ListChecks, Users, Lightbulb, BookOpen } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Button } from '@/components/ui/Button'
import { useCompare } from '@/hooks/useCompare'
import { useCompareStore } from '@/store/compareStore'
import VerdictCard from '@/components/compare/VerdictCard'
import ScoreRadar from '@/components/compare/ScoreRadar'
import ScoreBar from '@/components/compare/ScoreBar'
import HeadToHeadTable from '@/components/compare/HeadToHeadTable'
import AIComparisonLoading from '@/components/compare/AIComparisonLoading/AIComparisonLoading'
import { formatPrice } from '@/lib/utils'
import type { CarAnalysis } from '@/types/compare'

export default function CompareContent() {
  const t = useTranslations('Compare')
  const { ads } = useCompareStore()
  const { isLoading, statusText, progress, report, error, startComparison, reset } = useCompare()

  if (ads.length < 2 && !report) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <BarChart3 className="w-20 h-20 mx-auto text-text-muted mb-6" />
        <h1 className="text-2xl font-bold text-text-primary mb-3">
          {t('compareCars') || 'Compare Cars'}
        </h1>
        <p className="text-text-muted mb-8">
          {t('addCarsToCompare') || 'Add at least two cars to start comparing.'}
        </p>
        <Link href="/search">
          <Button variant="primary" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            {t('browseCars') || 'Browse Cars'}
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <>
      <AIComparisonLoading
        isLoading={isLoading}
        statusText={statusText}
        progress={progress}
        onCancel={reset}
      />

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-text-primary">
            {t('comparisonReport') || 'Comparison Report'}
          </h1>
          <Button variant="ghost" size="sm" onClick={reset}>
            {t('startOver') || 'Start Over'}
          </Button>
        </div>

        {report ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Trophy className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-text-primary">{t('verdict') || 'Verdict'}</h2>
            </div>
            <VerdictCard verdict={report.verdict} cars={report.cars} />
          </section>

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-text-primary">{t('scoreOverview') || 'Score Overview'}</h2>
            </div>
            <ScoreRadar cars={report.cars} />
          </section>

          <section className="space-y-4">
            {report.cars.map((car) => (
              <div key={car.ad_id} className="bg-surface rounded-xl border border-surface-border p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="relative w-16 h-12 rounded-lg overflow-hidden bg-surface-secondary flex-shrink-0">
                    <Image
                      src={car.cover_image_url || '/placeholder.svg'}
                      alt={`${car.brand} ${car.model}`}
                      fill
                      className="object-cover"
                      sizes="64px"
                    />
                  </div>
                  <div>
                    <h3 className="font-semibold text-text-primary">{car.brand} {car.model} {car.year}</h3>
                    <p className="text-sm text-text-muted">{formatPrice(car.price)} EGP &middot; {car.condition}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <ScoreBar label={t('valueForMoney') || 'Value for Money'} score={car.scores.value_for_money} />
                  <ScoreBar label={t('reliability') || 'Reliability'} score={car.scores.reliability} />
                  <ScoreBar label={t('runningCost') || 'Running Cost'} score={car.scores.running_cost} />
                  <ScoreBar label={t('resaleValue') || 'Resale Value'} score={car.scores.resale_value} />
                  <ScoreBar label={t('overall') || 'Overall'} score={car.scores.overall} />
                </div>
              </div>
            ))}
          </section>

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <ListChecks className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-text-primary">{t('headToHead') || 'Head to Head'}</h2>
            </div>
            <HeadToHeadTable cars={report.cars} />
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {report.cars.map((car) => (
              <div key={car.ad_id} className="bg-surface rounded-xl border border-surface-border p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-5 h-5 text-primary-500" />
                  <h3 className="font-semibold text-text-primary">{car.brand} {car.model}</h3>
                </div>
                <div className="space-y-3">
                  {car.photo_analysis && (
                    <div className="p-3 bg-blue-500/5 border border-blue-500/10 rounded-lg">
                      <h4 className="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-1">
                        {t('photoAnalysis') || 'Photo Analysis'}
                      </h4>
                      <p className="text-sm text-text-secondary leading-relaxed">{car.photo_analysis}</p>
                    </div>
                  )}
                  <div>
                    <h4 className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-1">{t('pros') || 'Pros'}</h4>
                    <ul className="space-y-1">
                      {car.pros.map((pro, i) => (
                        <li key={i} className="text-sm text-text-secondary flex items-start gap-1.5">
                          <span className="text-green-500 mt-0.5">+</span>
                          {pro}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-danger uppercase tracking-wide mb-1">{t('cons') || 'Cons'}</h4>
                    <ul className="space-y-1">
                      {car.cons.map((con, i) => (
                        <li key={i} className="text-sm text-text-secondary flex items-start gap-1.5">
                          <span className="text-danger mt-0.5">-</span>
                          {con}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </section>

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Users className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-text-primary">{t('buyerPersona') || 'Buyer Persona Match'}</h2>
            </div>
            <div className="space-y-3">
              {report.buyer_persona_match.map((match, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-surface-secondary rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-500 font-bold text-sm flex-shrink-0">
                    {(match.best_match_ad_id?.charAt(0)?.toUpperCase()) || '?'}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">{match.persona}</p>
                    <p className="text-xs text-text-muted mt-0.5">{match.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-text-primary">{t('keyDifferences') || 'Key Differences'}</h2>
            </div>
            <ul className="space-y-2">
              {report.key_differences.map((diff, i) => (
                <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5 flex-shrink-0" />
                  {diff}
                </li>
              ))}
            </ul>
          </section>

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Trophy className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-text-primary">{t('finalRecommendation') || 'Final Recommendation'}</h2>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">{report.final_recommendation}</p>
          </section>

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-text-primary">{t('researchSources') || 'Research Sources'}</h2>
            </div>
            <div className="space-y-4">
              {report.research_sources.map((source) => (
                <div key={source.ad_id}>
                  <p className="text-sm font-medium text-text-primary mb-2">{source.brand} {source.model}</p>
                  <ul className="space-y-1">
                    {source.sources.map((s, i) => (
                      <li key={i}>
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary-500 hover:underline"
                        >
                          {s.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        </motion.div>
      ) : error ? (
        <div className="text-center py-16">
          <p className="text-danger mb-4">{error}</p>
          <Button variant="primary" onClick={startComparison}>
            {t('retry') || 'Retry'}
          </Button>
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-text-muted mb-4">{t('readyToCompare') || 'Ready to compare?'}</p>
          <Button variant="primary" onClick={startComparison} className="gap-2">
            <BarChart3 className="w-4 h-4" />
            {t('startComparison') || 'Start Comparison'}
          </Button>
        </div>
      )}
    </div>
    </>
  )
}