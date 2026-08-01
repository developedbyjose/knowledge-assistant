"use client"

import { FormEvent, KeyboardEvent, useState } from "react"
import { Loader2Icon, SendIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

type ChatComposerProps = {
  disabled?: boolean
  isSending?: boolean
  onSend: (message: string) => Promise<void>
}

export function ChatComposer({
  disabled = false,
  isSending = false,
  onSend,
}: ChatComposerProps) {
  const [message, setMessage] = useState("")

  async function handleSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()
    const trimmed = message.trim()
    if (!trimmed || disabled || isSending) {
      return
    }

    setMessage("")
    await onSend(trimmed)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      void handleSubmit()
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t bg-background p-3"
    >
      <label className="sr-only" htmlFor="chat-message">
        Message
      </label>
      <Textarea
        id="chat-message"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a grounded question about the selected knowledge base"
        disabled={disabled || isSending}
        className="min-h-11 resize-none"
      />
      <Button
        type="submit"
        size="icon"
        aria-label="Send message"
        disabled={!message.trim() || disabled || isSending}
      >
        {isSending ? (
          <Loader2Icon className="size-4 animate-spin" />
        ) : (
          <SendIcon className="size-4" />
        )}
      </Button>
    </form>
  )
}
