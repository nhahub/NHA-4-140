import { useTranslations } from 'next-intl'
import { AdForm } from '@/components/ads/AdForm'

export default function NewAdPage() {
  const t = useTranslations('post_ad')

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-text-primary text-center mb-8">
        {t('title') || 'Post Your Ad'}
      </h1>
      <AdForm />
    </div>
  )
}
