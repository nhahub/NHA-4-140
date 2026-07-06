'use client'

import { useEffect, useRef, useState } from 'react'

const SMOOTHING = 0.25
const FFT_SIZE = 64

export function useAudioLevel(stream: MediaStream | null): number {
  const [amplitude, setAmplitude] = useState(0)
  const rafRef = useRef<number>(0)
  const smoothedRef = useRef(0)

  useEffect(() => {
    if (!stream) {
      setAmplitude(0)
      return
    }

    let audioContext: AudioContext | null = null
    let source: MediaStreamAudioSourceNode | null = null
    let analyser: AnalyserNode | null = null

    const init = () => {
      try {
        audioContext = new AudioContext()
        source = audioContext.createMediaStreamSource(stream)
        analyser = audioContext.createAnalyser()
        analyser.fftSize = FFT_SIZE
        source.connect(analyser)

        const dataArray = new Uint8Array(analyser.frequencyBinCount)

        const tick = () => {
          if (!analyser) return
          analyser.getByteTimeDomainData(dataArray)

          let sum = 0
          for (let i = 0; i < dataArray.length; i++) {
            const value = (dataArray[i] - 128) / 128
            sum += value * value
          }
          const rms = Math.sqrt(sum / dataArray.length)

          smoothedRef.current =
            smoothedRef.current * (1 - SMOOTHING) + rms * SMOOTHING

          setAmplitude(smoothedRef.current)

          rafRef.current = requestAnimationFrame(tick)
        }

        tick()
      } catch {
        // AudioContext may fail in some environments
      }
    }

    init()

    return () => {
      cancelAnimationFrame(rafRef.current)
      if (source) source.disconnect()
      if (analyser) analyser.disconnect()
      if (audioContext) audioContext.close()
      smoothedRef.current = 0
      setAmplitude(0)
    }
  }, [stream])

  return amplitude
}
