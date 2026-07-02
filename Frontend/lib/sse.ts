export type SSEEventCallback = (event: { type: string; content: any }) => void

export class SSEParser {
  private buffer: string = ''
  private abortController: AbortController | null = null

  async connect(
    url: string,
    body: object,
    callbacks: {
      onEvent: SSEEventCallback
      onDone: () => void
      onError: (err: string) => void
    }
  ): Promise<void> {
    this.abortController = new AbortController()

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: this.abortController.signal,
        credentials: 'include',
      })

      if (!response.ok) {
        callbacks.onError(`HTTP ${response.status}: ${response.statusText}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        callbacks.onError('No response body')
        return
      }

      const decoder = new TextDecoder()
      let done = false

      while (!done) {
        const { value, done: streamDone } = await reader.read()
        done = streamDone

        if (value) {
          this.buffer += decoder.decode(value, { stream: true })
          this.processBuffer(callbacks)
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        callbacks.onError(err.message || 'Connection error')
      }
    }
  }

  private processBuffer(callbacks: {
    onEvent: SSEEventCallback
    onDone: () => void
    onError: (err: string) => void
  }) {
    const lines = this.buffer.split('\n')
    this.buffer = lines.pop() || ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue

      if (trimmed.startsWith('data: ')) {
        const jsonStr = trimmed.slice(6)
        try {
          const event = JSON.parse(jsonStr)
          callbacks.onEvent(event)

          if (event.type === 'done') {
            callbacks.onDone()
          }
        } catch {
          // skip malformed JSON
        }
      }
    }
  }

  disconnect() {
    this.abortController?.abort()
  }
}
