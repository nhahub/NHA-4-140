'use client'

import dynamic from 'next/dynamic'

const CompareContent = dynamic(() => import('./CompareContent'), {
  ssr: false,
  loading: () => null,
})

export default function ComparePage() {
  return <CompareContent />
}