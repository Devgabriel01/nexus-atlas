import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../../store/useAppStore'
import { X, Terminal as TerminalIcon } from 'lucide-react'

export default function Terminal() {
  const { terminalOpen, setTerminalOpen, terminalLogs, clearLogs } = useAppStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [terminalLogs])

  return (
    <AnimatePresence>
      {terminalOpen && (
        <motion.div
          initial={{ y: '100%', opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: '100%', opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="absolute bottom-0 left-0 right-0 h-56 nexus-panel border-t border-nexus-border z-40 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-nexus-border bg-nexus-dark">
            <div className="flex items-center gap-2">
              <TerminalIcon size={12} className="text-nexus-cyan" />
              <span className="font-mono text-xs text-nexus-cyan tracking-widest">NEXUS CONSOLE</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={clearLogs}
                className="font-mono text-[10px] text-nexus-muted hover:text-nexus-text px-2"
              >
                CLR
              </button>
              <button
                onClick={() => setTerminalOpen(false)}
                className="text-nexus-muted hover:text-nexus-red transition-colors"
              >
                <X size={12} />
              </button>
            </div>
          </div>

          {/* Logs */}
          <div className="flex-1 overflow-y-auto p-3 space-y-0.5 font-mono text-[11px]">
            {terminalLogs.map((log, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-nexus-green leading-relaxed"
              >
                {log}
              </motion.div>
            ))}
            <div ref={bottomRef} />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
