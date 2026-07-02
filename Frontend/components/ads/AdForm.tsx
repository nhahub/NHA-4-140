'use client'

import { useState, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Upload, X, GripVertical, ChevronLeft, ChevronRight } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import {
  CONDITIONS,
  FUEL_TYPES,
  TRANSMISSIONS,
  BODY_TYPES,
  BODY_TYPE_ICONS,
} from '@/lib/utils'
import { api } from '@/lib/api'
import type { Ad } from '@/types/ad'

const BRANDS = [
  'Toyota', 'Hyundai', 'Nissan', 'BMW', 'Mercedes', 'Honda', 'Chevrolet', 'Kia',
  'Suzuki', 'Mitsubishi', 'Renault', 'Peugeot', 'Volkswagen', 'Ford', 'Jeep',
  'MG', 'Chery', 'BYD', 'Geely', 'Opel', 'Fiat', 'Audi', 'Lexus',
]

const CITIES = [
  'Cairo', 'Alexandria', 'Giza', 'Mansoura', 'Tanta', 'Port Said',
  'Suez', 'Luxor', 'Aswan', 'Hurghada', 'Sharm el-Sheikh',
  '6th of October', 'Sheikh Zayed', 'New Cairo', 'Madinaty',
]

const CC_RANGES = ['1000-1500', '1500-2000', '2000-3000', '3000+']

const CURRENT_YEAR = 2026
const YEARS = Array.from({ length: CURRENT_YEAR - 1989 }, (_, i) => CURRENT_YEAR - i)

const COLOR_OPTIONS = [
  'White', 'Black', 'Silver', 'Gray', 'Blue', 'Red', 'Green',
  'Beige', 'Brown', 'Gold', 'Orange', 'Yellow', 'Burgundy',
]

const formSchema = z.object({
  brand: z.string().min(1, 'Brand is required'),
  model: z.string().min(1, 'Model is required'),
  year: z.coerce.number().int().min(1990, 'Invalid year').max(CURRENT_YEAR, 'Invalid year'),
  condition: z.enum(CONDITIONS, { required_error: 'Condition is required' }),
  price: z.coerce.number().positive('Price must be greater than 0'),
  km_driven: z.coerce.number().positive('KM must be greater than 0'),
  transmission: z.enum(TRANSMISSIONS, { required_error: 'Transmission is required' }),
  fuel_type: z.enum(FUEL_TYPES, { required_error: 'Fuel type is required' }),
  body_type: z.enum(BODY_TYPES, { required_error: 'Body type is required' }),
  cc_range: z.string().min(1, 'CC range is required'),
  color: z.string().min(1, 'Color is required'),
  city: z.string().min(1, 'City is required'),
  description: z
    .string()
    .min(50, 'Description must be at least 50 characters'),
})

type FormValues = z.infer<typeof formSchema>

interface AdFormProps {
  isEdit?: boolean
  initialData?: Partial<Ad>
}

export function AdForm({ isEdit, initialData }: AdFormProps) {
  const t = useTranslations('post_ad')
  const [step, setStep] = useState(1)
  const [files, setFiles] = useState<File[]>([])
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const idempotencyKey = useRef(crypto.randomUUID())

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: initialData
      ? {
          brand: initialData.brand || '',
          model: initialData.model || '',
          year: initialData.year || CURRENT_YEAR,
          condition: (initialData.condition as any) || 'used',
          price: initialData.price || undefined,
          km_driven: initialData.km_driven || undefined,
          transmission: (initialData.transmission as any) || 'automatic',
          fuel_type: (initialData.fuel_type as any) || 'petrol',
          body_type: (initialData.body_type as any) || 'sedan',
          cc_range: initialData.cc_range || '',
          color: initialData.color || '',
          city: initialData.city || '',
          description: initialData.description || '',
        }
      : {
          brand: '',
          model: '',
          year: CURRENT_YEAR,
          condition: 'used',
          price: undefined,
          km_driven: undefined,
          transmission: 'automatic',
          fuel_type: 'petrol',
          body_type: 'sedan',
          cc_range: '',
          color: '',
          city: '',
          description: '',
        },
  })

  const description = watch('description')
  const descriptionLength = description?.length || 0
  const descRemaining = Math.max(0, 50 - descriptionLength)

  const onDrop = useCallback((accepted: File[]) => {
    setFiles((prev) => {
      const combined = [...prev, ...accepted]
      return combined.slice(0, 10)
    })
  }, [])

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const moveFile = (from: number, to: number) => {
    setFiles((prev) => {
      const next = [...prev]
      const [moved] = next.splice(from, 1)
      next.splice(to, 0, moved)
      return next
    })
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] },
    maxSize: 5 * 1024 * 1024,
    maxFiles: 10,
    disabled: files.length >= 10,
  })

  const renderStepIndicator = () => (
    <div className="flex items-center gap-2 mb-8">
      {[1, 2, 3].map((s) => (
        <div key={s} className="flex items-center flex-1">
          <div
            className={cn(
              'flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-colors',
              step === s
                ? 'bg-primary-500 text-white'
                : step > s
                  ? 'bg-primary-100 text-primary-500'
                  : 'bg-surface-secondary text-text-muted'
            )}
          >
            {step > s ? '✓' : s}
          </div>
          <span
            className={cn(
              'ml-2 text-sm hidden sm:inline',
              step === s ? 'text-text-primary font-medium' : 'text-text-muted'
            )}
          >
            {t(`step_${s}`)}
          </span>
          {s < 3 && (
            <div
              className={cn(
                'flex-1 h-0.5 mx-3',
                step > s ? 'bg-primary-500' : 'bg-surface-border'
              )}
            />
          )}
        </div>
      ))}
    </div>
  )

  const renderStep1 = () => (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            {t('brand')}
          </label>
          <select
            className={cn(
              'w-full h-10 px-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
            )}
            {...register('brand')}
          >
            <option value="">Select brand</option>
            {BRANDS.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
          {errors.brand && (
            <p className="mt-1 text-xs text-danger">{errors.brand.message}</p>
          )}
        </div>
        <Input
          label={t('model')}
          id="model"
          placeholder="e.g. Corolla"
          error={errors.model?.message}
          {...register('model')}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            {t('year')}
          </label>
          <select
            className={cn(
              'w-full h-10 px-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
            )}
            {...register('year')}
          >
            {YEARS.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          {errors.year && (
            <p className="mt-1 text-xs text-danger">{errors.year.message}</p>
          )}
        </div>
        <Input
          label={t('price_egp')}
          id="price"
          type="number"
          placeholder="e.g. 500000"
          error={errors.price?.message}
          {...register('price')}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('condition')}
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {CONDITIONS.map((c) => (
            <label
              key={c}
              className={cn(
                'flex flex-col items-center gap-1 p-3 rounded-lg border cursor-pointer transition-colors',
                watch('condition') === c
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-surface-border hover:border-text-muted'
              )}
            >
              <input
                type="radio"
                value={c}
                className="sr-only"
                {...register('condition')}
              />
              <span className="text-sm font-medium capitalize text-text-primary">
                {t(`condition_${c}`)}
              </span>
            </label>
          ))}
        </div>
        {errors.condition && (
          <p className="mt-1 text-xs text-danger">{errors.condition.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          label={t('km_driven')}
          id="km_driven"
          type="number"
          placeholder="e.g. 50000"
          error={errors.km_driven?.message}
          {...register('km_driven')}
        />
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            CC Range
          </label>
          <select
            className={cn(
              'w-full h-10 px-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
            )}
            {...register('cc_range')}
          >
            <option value="">Select CC range</option>
            {CC_RANGES.map((r) => (
              <option key={r} value={r}>
                {r} cc
              </option>
            ))}
          </select>
          {errors.cc_range && (
            <p className="mt-1 text-xs text-danger">{errors.cc_range.message}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          Transmission
        </label>
        <div className="flex gap-4">
          {TRANSMISSIONS.map((tr) => (
            <label
              key={tr}
              className={cn(
                'flex items-center justify-center gap-2 flex-1 p-3 rounded-lg border cursor-pointer transition-colors',
                watch('transmission') === tr
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-surface-border hover:border-text-muted'
              )}
            >
              <input
                type="radio"
                value={tr}
                className="sr-only"
                {...register('transmission')}
              />
              <span className="text-sm font-medium capitalize text-text-primary">
                {tr}
              </span>
            </label>
          ))}
        </div>
        {errors.transmission && (
          <p className="mt-1 text-xs text-danger">{errors.transmission.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          Fuel Type
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {FUEL_TYPES.map((f) => (
            <label
              key={f}
              className={cn(
                'flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors',
                watch('fuel_type') === f
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-surface-border hover:border-text-muted'
              )}
            >
              <input
                type="radio"
                value={f}
                className="sr-only"
                {...register('fuel_type')}
              />
              <span className="text-sm font-medium capitalize text-text-primary">
                {f}
              </span>
            </label>
          ))}
        </div>
        {errors.fuel_type && (
          <p className="mt-1 text-xs text-danger">{errors.fuel_type.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          Body Type
        </label>
        <div className="grid grid-cols-4 sm:grid-cols-7 gap-3">
          {BODY_TYPES.map((b) => (
            <label
              key={b}
              className={cn(
                'flex flex-col items-center gap-1 p-3 rounded-lg border cursor-pointer transition-colors',
                watch('body_type') === b
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-surface-border hover:border-text-muted'
              )}
            >
              <input
                type="radio"
                value={b}
                className="sr-only"
                {...register('body_type')}
              />
              <span className="text-lg">{BODY_TYPE_ICONS[b]}</span>
              <span className="text-xs font-medium capitalize text-text-primary">
                {b}
              </span>
            </label>
          ))}
        </div>
        {errors.body_type && (
          <p className="mt-1 text-xs text-danger">{errors.body_type.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Color
          </label>
          <select
            className={cn(
              'w-full h-10 px-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
            )}
            {...register('color')}
          >
            <option value="">Select color</option>
            {COLOR_OPTIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          {errors.color && (
            <p className="mt-1 text-xs text-danger">{errors.color.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            City
          </label>
          <select
            className={cn(
              'w-full h-10 px-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
            )}
            {...register('city')}
          >
            <option value="">Select city</option>
            {CITIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          {errors.city && (
            <p className="mt-1 text-xs text-danger">{errors.city.message}</p>
          )}
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          Description
        </label>
        <textarea
          className={cn(
            'w-full min-h-[200px] p-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
            'placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'transition-colors resize-vertical',
            errors.description && 'border-danger focus:ring-danger'
          )}
          placeholder={t('description_placeholder')}
          rows={6}
          {...register('description')}
        />
        <p
          className={cn(
            'mt-1 text-xs text-right',
            descriptionLength < 50 ? 'text-danger' : 'text-text-muted'
          )}
        >
          {t('description_min', { count: descRemaining })}
        </p>
        {errors.description && (
          <p className="mt-1 text-xs text-danger">{errors.description.message}</p>
        )}
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-surface-border hover:border-primary-500 hover:bg-surface-secondary'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-10 h-10 mx-auto text-text-muted mb-3" />
        <p className="text-sm text-text-primary font-medium">
          {t('photos_drag')}
        </p>
        <p className="text-xs text-text-muted mt-1">{t('photos_max')}</p>
      </div>

      {files.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="relative group aspect-[4/3] rounded-lg overflow-hidden border border-surface-border"
            >
              <img
                src={URL.createObjectURL(file)}
                alt={`Upload ${i + 1}`}
                className="w-full h-full object-cover"
              />
              {i === 0 && (
                <span className="absolute top-1 left-1 bg-primary-500 text-white text-[10px] px-1.5 py-0.5 rounded">
                  {t('photos_cover')}
                </span>
              )}
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                <button
                  type="button"
                  onClick={() => {
                    if (i > 0) moveFile(i, i - 1)
                  }}
                  disabled={i === 0}
                  className="p-1.5 bg-white rounded-full disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4 text-text-primary" />
                </button>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  className="p-1.5 bg-danger rounded-full"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (i < files.length - 1) moveFile(i, i + 1)
                  }}
                  disabled={i === files.length - 1}
                  className="p-1.5 bg-white rounded-full disabled:opacity-30"
                >
                  <ChevronRight className="w-4 h-4 text-text-primary" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {files.length === 0 && !isEdit && (
        <p className="text-xs text-text-muted text-center">
          You need to upload at least one photo
        </p>
      )}
    </div>
  )

  const onSubmit = async (data: FormValues) => {
    if (isSubmitting) return
    setSubmitError(null)
    if (files.length === 0 && !isEdit) {
      setSubmitError('Please upload at least one photo')
      return
    }
    setIsSubmitting(true)
    try {
      const formData = new FormData()
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          formData.append(key, String(value))
        }
      })
      files.forEach((file) => {
        formData.append('files', file)
      })
      if (isEdit && initialData?.id) {
        await api.patchForm(`/ads/${initialData.id}`, formData)
      } else {
        await api.postForm('/ads', formData, {
          headers: { 'X-Idempotency-Key': idempotencyKey.current },
        })
      }
      router.push('/')
    } catch {
      setSubmitError('Failed to submit ad. Please try again.')
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit, () => setStep(1))} className="max-w-3xl mx-auto">
      {renderStepIndicator()}

      <div className="bg-surface border border-surface-border rounded-xl p-6">
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
      </div>

      <div className="flex items-center justify-between mt-6">
        <div>
          {step > 1 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep(step - 1)}
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </Button>
          )}
        </div>
        <div className="flex gap-3">
          {step < 3 ? (
            <Button
              type="button"
              onClick={() => setStep(step + 1)}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          ) : (
            <div className="flex flex-col items-end gap-2">
              {submitError && (
                <p className="text-sm text-danger">{submitError}</p>
              )}
              {Object.keys(errors).length > 0 && (
                <p className="text-sm text-danger">
                  Please fix {Object.keys(errors).length} error(s) above, then try again
                </p>
              )}
              <Button type="submit" isLoading={isSubmitting}>
                {isEdit ? 'Update Ad' : 'Submit Ad'}
              </Button>
            </div>
          )}
        </div>
      </div>
    </form>
  )
}
