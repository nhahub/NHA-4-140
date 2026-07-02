'use client'

import { CheckCircle, XCircle, Minus } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { cn, formatPrice } from '@/lib/utils'
import type { CarAnalysis } from '@/types/compare'

interface HeadToHeadTableProps {
  cars: CarAnalysis[]
}

interface RowDef {
  labelKey: string
  getValue: (car: CarAnalysis) => string | number
  compare: (values: (string | number)[]) => number[]
}

export default function HeadToHeadTable({ cars }: HeadToHeadTableProps) {
  const t = useTranslations('Compare')

  const rows: RowDef[] = [
    {
      labelKey: 'price',
      getValue: (c) => formatPrice(c.price),
      compare: (values) => {
        const nums = values.map((v) => {
          if (typeof v === 'number') return v
          return parseFloat(String(v).replace(/[^0-9.]/g, '')) || 0
        })
        const min = Math.min(...nums)
        return nums.map((n) => (n === min ? 1 : 0))
      },
    },
    {
      labelKey: 'year',
      getValue: (c) => c.year,
      compare: (values) => {
        const nums = values.map((v) => (typeof v === 'number' ? v : 0))
        const max = Math.max(...nums)
        return nums.map((n) => (n === max ? 1 : 0))
      },
    },
    {
      labelKey: 'condition',
      getValue: (c) => c.condition,
      compare: (values) => {
        const rank: Record<string, number> = { new: 2, used: 1 }
        const nums = values.map((v) => rank[String(v)] ?? 0)
        const max = Math.max(...nums)
        return nums.map((n) => (n === max ? 1 : 0))
      },
    },
    {
      labelKey: 'spareParts',
      getValue: (c) => c.spare_parts_availability ?? '-',
      compare: (values) => {
        const rank: Record<string, number> = {
          Abundant: 3,
          Available: 2,
          Limited: 1,
          Scarce: 0,
        }
        const nums = values.map((v) => rank[String(v)] ?? 0)
        const max = Math.max(...nums)
        return nums.map((n) => (n === max && max > 0 ? 1 : 0))
      },
    },
    {
      labelKey: 'serviceCenters',
      getValue: (c) => c.service_centers_egypt ?? '-',
      compare: (values) => {
        const rank: Record<string, number> = {
          Many: 3,
          Adequate: 2,
          Few: 1,
          None: 0,
        }
        const nums = values.map((v) => rank[String(v)] ?? 0)
        const max = Math.max(...nums)
        return nums.map((n) => (n === max && max > 0 ? 1 : 0))
      },
    },
  ]

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            <th className="p-3 text-left font-medium text-muted-foreground" />
            {cars.map((car, idx) => (
              <th
                key={car.ad_id}
                className={cn(
                  'p-3 text-center font-semibold',
                  idx === 0 && 'text-primary-500',
                  idx === 1 && 'text-orange-500',
                  idx === 2 && 'text-green-500',
                )}
              >
                {car.brand} {car.model}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const values = cars.map(row.getValue)
            const winners = row.compare(values)

            return (
              <tr key={row.labelKey} className="border-b border-border">
                <td className="p-3 font-medium text-muted-foreground">
                  {t(row.labelKey)}
                </td>
                {values.map((val, idx) => {
                  const isWinner = winners[idx] === 1

                  return (
                    <td
                      key={idx}
                      className={cn(
                        'p-3 text-center transition-colors',
                        isWinner && 'bg-green-50',
                      )}
                    >
                      <span className="inline-flex items-center gap-1.5">
                        {winners.length > 0 && (
                          <>
                            {isWinner ? (
                              <CheckCircle className="h-4 w-4 shrink-0 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 shrink-0 text-muted-foreground/40" />
                            )}
                          </>
                        )}
                        {val}
                      </span>
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
