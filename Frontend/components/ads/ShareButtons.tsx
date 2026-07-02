'use client'

import { Heart, MessageCircle } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { formatPrice } from '@/lib/utils'
import type { Ad } from '@/types/ad'

interface ShareButtonsProps {
  ad: Ad
}

export function ShareButtons({ ad }: ShareButtonsProps) {
  const [isSaved, setIsSaved] = useState(false)
  const shareText = `Check out this ${ad.brand} ${ad.model} ${ad.year} for ${formatPrice(ad.price)} EGP!`
  const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(shareText + ' ' + window.location.href)}`

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        className="flex-1 gap-2"
        onClick={() => setIsSaved(!isSaved)}
      >
        <Heart className={`w-4 h-4 ${isSaved ? 'fill-danger text-danger' : ''}`} />
        {isSaved ? 'Saved' : 'Save'}
      </Button>
      <a
        href={whatsappUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center justify-center h-10 px-3 rounded-lg border-2 border-green-500 text-green-600 hover:bg-green-50 transition-colors font-medium text-sm gap-2"
      >
        <MessageCircle className="w-4 h-4" />
        WhatsApp
      </a>
    </div>
  )
}
