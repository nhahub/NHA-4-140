import type { Metadata, Viewport } from 'next'
import { Inter, Cairo } from 'next/font/google'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { Navbar } from '@/components/layout/Navbar'
import { MobileNav } from '@/components/layout/MobileNav'
import { Footer } from '@/components/layout/Footer'
import { ChatBubble } from '@/components/chat/ChatBubble'
import { ChatDrawer } from '@/components/chat/ChatDrawer'
import { CompareTray } from '@/components/layout/CompareTray'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })
const cairo = Cairo({ subsets: ['arabic'], variable: '--font-arabic' })

export const metadata: Metadata = {
  title: 'CarsMarket Egypt - Find Your Perfect Car',
  description:
    "Egypt's AI-powered car marketplace. Find your perfect car with smart search, compare listings, and get expert advice from our AI assistant.",
  icons: {
    icon: '/favicon.svg',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const messages = await getMessages()

  return (
    <html lang="en" dir="ltr" className={`${inter.variable} ${cairo.variable}`}>
      <body className="font-sans min-h-screen bg-surface-secondary">
        <NextIntlClientProvider messages={messages}>
          <Navbar />
          <div className="pb-14 md:pb-0">
            {children}
          </div>
          <MobileNav />
          <Footer />
          <ChatBubble />
          <ChatDrawer />
          <CompareTray />
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
