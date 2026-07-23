import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Bot, Moon, RefreshCw, SendHorizontal, Square, Sun, User } from 'lucide-react'
import { endpoints } from '../lib/api'
import { useTheme } from '../lib/theme'

interface Message {
  role: 'user' | 'assistant'
  text: string
  isError?: boolean
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const queryClient = useQueryClient()
  const { theme, toggleTheme } = useTheme()

  const statusQuery = useQuery({
    queryKey: ['sync-status'],
    queryFn: endpoints.syncStatus,
    // Poll while a sync is running so the banner updates without a manual refresh.
    refetchInterval: (query) => (query.state.data?.sync_in_progress ? 2000 : false),
  })

  const syncMutation = useMutation({
    mutationFn: endpoints.triggerSync,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sync-status'] }),
  })

  const chatMutation = useMutation({
    mutationFn: (message: string) => {
      const controller = new AbortController()
      abortControllerRef.current = controller
      return endpoints.chat(message, controller.signal)
    },
  })

  function handleStop() {
    abortControllerRef.current?.abort()
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatMutation.isPending])

  async function handleSend() {
    const question = input.trim()
    if (!question || chatMutation.isPending) return
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setInput('')
    try {
      const { answer } = await chatMutation.mutateAsync(question)
      setMessages((prev) => [...prev, { role: 'assistant', text: answer }])
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return
      }
      const message = err instanceof Error ? err.message : 'Something went wrong.'
      setMessages((prev) => [...prev, { role: 'assistant', text: `Error: ${message}`, isError: true }])
    }
  }

  const status = statusQuery.data
  const lastSynced = status?.last_synced_at
    ? new Date(status.last_synced_at).toLocaleString()
    : 'never'

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      <header className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-border px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Bot className="h-3.5 w-3.5" />
          </div>
          <span className="text-sm font-semibold">allocator-qa</span>
          <span className="text-xs text-muted-foreground">Investor &amp; fund data assistant</span>
        </div>
        <button
          className="al-btn al-btn--ghost al-btn--icon"
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
      </header>

      <main className="flex flex-1 flex-col gap-3 overflow-hidden p-4">
        <div className="al-card flex flex-wrap items-center justify-between gap-3 p-3">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span>
              Last synced: <strong className="text-foreground">{lastSynced}</strong>
            </span>
            {status ? (
              <span className="al-badge al-badge--info">
                {status.row_counts.investors ?? 0} investors
              </span>
            ) : null}
            {status ? (
              <span className="al-badge al-badge--info">{status.row_counts.funds ?? 0} funds</span>
            ) : null}
            {status?.sync_in_progress ? (
              <span className="al-badge al-badge--warning">
                <span className="al-badge__dot al-animate-pulse-dot" />
                Syncing…
              </span>
            ) : null}
          </div>
          <button
            className="al-btn al-btn--primary al-btn--sm"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending || status?.sync_in_progress}
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${status?.sync_in_progress ? 'animate-spin' : ''}`}
            />
            {status?.sync_in_progress ? 'Syncing…' : 'Sync now'}
          </button>
        </div>

        <div className="al-card flex flex-1 flex-col overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="al-empty flex-1">
              <Bot className="al-empty__icon" />
              <p className="al-empty__title">Ask about investors or funds</p>
              <p className="al-empty__description">
                e.g. &quot;Who has the highest investment with us?&quot; Answers are based only on
                the local cache above — click &quot;Sync now&quot; first if you want the latest
                data.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {messages.map((message, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2.5 ${
                    message.role === 'user' ? 'flex-row-reverse self-end' : 'self-start'
                  }`}
                >
                  <div
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                      message.role === 'user'
                        ? 'bg-secondary text-secondary-foreground'
                        : 'bg-primary text-primary-foreground'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <User className="h-3.5 w-3.5" />
                    ) : (
                      <Bot className="h-3.5 w-3.5" />
                    )}
                  </div>
                  <div
                    className={`al-chat-bubble max-w-[75%] rounded-lg px-3.5 py-2.5 text-sm ${
                      message.role === 'user'
                        ? 'bg-secondary text-secondary-foreground'
                        : message.isError
                          ? 'al-callout'
                          : 'bg-muted text-foreground'
                    }`}
                  >
                    {message.role === 'assistant' ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.text}</p>
                    )}
                  </div>
                </div>
              ))}
              {chatMutation.isPending ? (
                <div className="flex items-start gap-2.5">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <Bot className="h-3.5 w-3.5" />
                  </div>
                  <div className="al-chat-bubble flex items-center gap-1 rounded-lg bg-muted px-3.5 py-3">
                    <span className="al-typing-dot" />
                    <span className="al-typing-dot" />
                    <span className="al-typing-dot" />
                  </div>
                </div>
              ) : null}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            void handleSend()
          }}
        >
          <input
            className="al-input flex-1"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about investors or funds…"
          />
          {chatMutation.isPending ? (
            <button
              className="al-btn al-btn--destructive al-btn--icon"
              type="button"
              onClick={handleStop}
              aria-label="Stop"
              title="Stop generating"
            >
              <Square className="h-4 w-4" />
            </button>
          ) : (
            <button
              className="al-btn al-btn--primary al-btn--icon"
              type="submit"
              disabled={!input.trim()}
              aria-label="Send"
            >
              <SendHorizontal className="h-4 w-4" />
            </button>
          )}
        </form>
      </main>
    </div>
  )
}
