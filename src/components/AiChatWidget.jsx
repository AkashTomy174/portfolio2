import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { BotIcon, MessageSquareIcon, PauseIcon, PlayIcon, SendIcon, XIcon, LinkedinIcon, GithubIcon } from './Icons';
import { useReducedMotion } from '../contexts/MotionPrefsContext';
import { SITE } from '../siteConfig';

const AI_ENDPOINT = import.meta.env.VITE_AI_CHAT_ENDPOINT || '/api/ai-chat';
const VOICE_ENABLED = import.meta.env.VITE_AI_CHAT_VOICE === 'true';

const SUGGESTED_PROMPTS = [
  'What is EasyBuy and what did you build?',
  "What's your experience with Django and AWS?",
  'What makes you different from other developers?',
  'Are you open to full-time roles?',
  "What's your strongest technical skill?",
];

const INITIAL_MESSAGES = [
  {
    id: 'intro',
    role: 'assistant',
    text: "Hi, I'm AI Akash. Ask me about Akash's projects, backend work, AWS experience, or role fit.",
  },
];

const makeId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const normalizeAudioUrl = (audioUrl) => {
  if (!audioUrl) return null;
  if (/^https?:\/\//i.test(audioUrl)) return audioUrl;
  return audioUrl.startsWith('/') ? audioUrl : `/${audioUrl}`;
};

const linkify = (text) => {
  const urlRegex = /(https?:\/\/[^\s]+|(?:www\.)[^\s]+|github\.com\/[^\s]+|linkedin\.com\/[^\s]+|easybuy\.akashtomy\.com[^\s]*)/gi;
  const parts = text.split(urlRegex);
  return parts.map((part, i) => {
    if (urlRegex.test(part)) {
      const href = part.startsWith('http') ? part : `https://${part}`;
      return (
        <a
          key={i}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-600 underline underline-offset-2 hover:text-violet-800 transition-colors"
        >
          {part}
        </a>
      );
    }
    return part;
  });
};

const ChatMessage = ({ message, onPlayAudio, isPlaying }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
          isUser
            ? 'bg-accent-dark text-white rounded-br-md'
            : 'bg-white border border-black/8 text-accent-dark rounded-bl-md'
        }`}
      >
        <p>{isUser ? message.text : linkify(message.text)}</p>
        {message.audioUrl && !isUser && (
          <button
            type="button"
            onClick={() => onPlayAudio(message.audioUrl)}
            className="interactive mt-3 inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700 transition-colors hover:bg-violet-100"
          >
            {isPlaying ? <PauseIcon className="h-3.5 w-3.5" /> : <PlayIcon className="h-3.5 w-3.5" />}
            {isPlaying ? 'Pause response' : 'Play response'}
          </button>
        )}
      </div>
    </div>
  );
};

const LoadingBubble = () => (
  <div className="flex justify-start">
    <div className="rounded-2xl rounded-bl-md border border-black/8 bg-white px-4 py-3 shadow-sm">
      <div className="flex items-center gap-1.5" aria-label="AI Akash is typing">
        {[0, 1, 2].map((dot) => (
          <span
            key={dot}
            className="h-2 w-2 rounded-full bg-accent-gray/45 animate-pulse"
            style={{ animationDelay: `${dot * 120}ms` }}
          />
        ))}
      </div>
    </div>
  </div>
);

const AiChatWidget = () => {
  const reduced = useReducedMotion();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [playingUrl, setPlayingUrl] = useState(null);
  const audioRef = useRef(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [isOpen]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: reduced ? 'auto' : 'smooth',
    });
  }, [messages, isLoading, reduced]);

  const submitMessage = async (value = input) => {
    const text = value.trim();
    if (!text || isLoading) return;

    const userMessage = { id: makeId(), role: 'user', text };
    setMessages((current) => [...current, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(AI_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, voice: VOICE_ENABLED }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.message || 'AI is temporarily unavailable.');
      }

      setMessages((current) => [
        ...current,
        {
          id: makeId(),
          role: 'assistant',
          text: payload.text || "I don't have that information yet. Reach out to Akash directly.",
          audioUrl: normalizeAudioUrl(payload.audio_url),
          sources: payload.sources || [],
          cached: Boolean(payload.cached),
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: makeId(),
          role: 'assistant',
          text: error.message || 'AI Akash is temporarily unavailable. Please try again in a bit.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlayAudio = (audioUrl) => {
    const audio = audioRef.current;
    if (!audio) return;

    if (playingUrl === audioUrl && !audio.paused) {
      audio.pause();
      setPlayingUrl(null);
      return;
    }

    audio.src = audioUrl;
    audio.play()
      .then(() => setPlayingUrl(audioUrl))
      .catch(() => setPlayingUrl(null));
  };

  return (
    <div className="fixed bottom-5 right-5 z-[9000] sm:bottom-6 sm:right-6">
      <audio ref={audioRef} onEnded={() => setPlayingUrl(null)} onPause={() => setPlayingUrl(null)} />

      <AnimatePresence>
        {isOpen && (
          <motion.section
            id="ai-akash-chat"
            initial={reduced ? { opacity: 1 } : { opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0, y: 16, scale: 0.98 }}
            transition={{ duration: reduced ? 0 : 0.22, ease: [0.16, 1, 0.3, 1] }}
            className="mb-4 flex h-[min(640px,calc(100vh-7rem))] w-[calc(100vw-2.5rem)] max-w-[390px] flex-col overflow-hidden rounded-2xl border border-black/10 bg-[#f8f8f8]/95 shadow-[0_24px_80px_rgba(0,0,0,0.22)] backdrop-blur-2xl"
            aria-label="AI Akash chat"
          >
            <header className="flex items-center justify-between border-b border-black/8 bg-white/80 px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-dark text-white">
                  <BotIcon className="h-5 w-5" aria-hidden="true" />
                </span>
                <div>
                  <h2 className="text-sm font-black text-accent-dark">AI Akash</h2>
                  <p className="text-xs font-medium text-accent-gray">Portfolio assistant</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <a
                  href={SITE.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="interactive p-2 rounded-full text-accent-gray hover:text-blue-500 hover:bg-blue-50 transition-colors"
                  aria-label="LinkedIn"
                >
                  <LinkedinIcon className="h-4 w-4" aria-hidden="true" />
                </a>
                <a
                  href={SITE.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="interactive p-2 rounded-full text-accent-gray hover:text-violet-600 hover:bg-violet-50 transition-colors"
                  aria-label="GitHub"
                >
                  <GithubIcon className="h-4 w-4" aria-hidden="true" />
                </a>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="interactive rounded-full p-2 text-accent-gray transition-colors hover:bg-black/5 hover:text-accent-dark"
                  aria-label="Close AI Akash chat"
                >
                  <XIcon className="h-4 w-4" aria-hidden="true" />
                </button>
              </div>
            </header>

            <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onPlayAudio={handlePlayAudio}
                  isPlaying={playingUrl === message.audioUrl}
                />
              ))}
              {messages.length === INITIAL_MESSAGES.length && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => submitMessage(prompt)}
                      className="interactive rounded-full border border-black/10 bg-white px-3 py-1.5 text-left text-xs font-semibold text-accent-gray transition-all hover:border-violet-300 hover:text-violet-700"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              )}
              {isLoading && <LoadingBubble />}
            </div>

            <form
              className="border-t border-black/8 bg-white/90 p-3"
              onSubmit={(event) => {
                event.preventDefault();
                submitMessage();
              }}
            >
              <div className="flex items-end gap-2 rounded-2xl border border-black/10 bg-white p-2 shadow-sm focus-within:border-violet-300">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      submitMessage();
                    }
                  }}
                  rows={1}
                  maxLength={500}
                  placeholder="Ask about Akash..."
                  className="max-h-24 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-sm text-accent-dark outline-none placeholder:text-accent-gray/55"
                  aria-label="Message AI Akash"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="interactive flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-dark text-white transition-all hover:bg-accent-purple disabled:cursor-not-allowed disabled:bg-accent-light disabled:text-accent-gray"
                  aria-label="Send message"
                >
                  <SendIcon className="h-4 w-4" aria-hidden="true" />
                </button>
              </div>
            </form>
          </motion.section>
        )}
      </AnimatePresence>

      <motion.button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        whileHover={reduced ? {} : { y: -2, scale: 1.03 }}
        whileTap={reduced ? {} : { scale: 0.96 }}
        className="interactive flex items-center gap-3 rounded-full bg-accent-dark px-5 py-4 text-sm font-bold text-white shadow-[0_12px_40px_rgba(17,17,17,0.28)] transition-colors hover:bg-accent-purple"
        aria-expanded={isOpen}
        aria-controls="ai-akash-chat"
      >
        <MessageSquareIcon className="h-5 w-5" aria-hidden="true" />
        Ask AI Akash
      </motion.button>
    </div>
  );
};

export default AiChatWidget;
