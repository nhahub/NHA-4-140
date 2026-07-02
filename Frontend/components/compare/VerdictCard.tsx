'use client'

import { Trophy, Award } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Button } from '@/components/ui/Button'
import { formatPrice } from '@/lib/utils'
import type { Verdict, CarAnalysis } from '@/types/compare'

interface VerdictCardProps {
  verdict: Verdict
  cars: CarAnalysis[]
}

export default function VerdictCard({ verdict, cars }: VerdictCardProps) {
  const t = useTranslations('Compare')

  const winner = cars.find((c) => c.ad_id === verdict.winner_ad_id)
  const runnerUp = cars.find((c) => c.ad_id === verdict.runner_up_ad_id)

  if (!winner) return null

  return (
    <div className="space-y-4">
      {/* Winner */}
      <div className="rounded-lg border-2 border-primary p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <Trophy className="h-5 w-5 text-primary" />
          <span className="rounded-md bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
            {t('recommended')}
          </span>
        </div>

        <h3 className="text-lg font-bold">{winner.brand} {winner.model}</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          {formatPrice(winner.price)}
        </p>

        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{t('confidence')}:</span>
          <span className="text-sm font-semibold">{verdict.confidence === 'high' ? '90%' : verdict.confidence === 'medium' ? '70%' : '50%'}</span>
        </div>

        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {verdict.reasoning}
        </p>

        <Button className="mt-4 w-full" asChild>
          <a href={`/cars/${winner.ad_id}`}>{t('viewDetails')}</a>
        </Button>
      </div>

      {/* Runner-up */}
      {runnerUp && (
        <div className="rounded-lg border border-muted p-4">
          <div className="mb-2 flex items-center gap-2">
            <Award className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">
              {t('runnerUp')}
            </span>
          </div>

          <h4 className="text-base font-semibold">{runnerUp.brand} {runnerUp.model}</h4>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {formatPrice(runnerUp.price)}
          </p>

          <Button variant="outline" className="mt-3 w-full" asChild>
            <a href={`/cars/${runnerUp.ad_id}`}>{t('viewDetails')}</a>
          </Button>
        </div>
      )}
    </div>
  )
}
