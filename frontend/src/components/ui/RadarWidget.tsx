import { motion } from 'framer-motion'

interface Props {
  anomalyCount?: number
}

export default function RadarWidget({ anomalyCount = 0 }: Props) {
  return (
    <div className="relative w-32 h-32 flex items-center justify-center">
      {/* Outer rings */}
      {[1, 0.66, 0.33].map((scale, i) => (
        <div
          key={i}
          className="absolute rounded-full border border-nexus-cyan/20"
          style={{ width: `${scale * 100}%`, height: `${scale * 100}%` }}
        />
      ))}

      {/* Cross hairs */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-full h-px bg-nexus-cyan/15" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-full w-px bg-nexus-cyan/15" />
      </div>

      {/* Spinning sweep */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-0"
        style={{ transformOrigin: 'center' }}
      >
        <div
          className="absolute top-1/2 left-1/2 w-1/2 h-px origin-left"
          style={{
            background: 'linear-gradient(to right, rgba(0,212,255,0.7), transparent)',
          }}
        />
        {/* Sweep gradient */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: 'conic-gradient(from 0deg, rgba(0,212,255,0.15) 0deg, transparent 60deg)',
          }}
        />
      </motion.div>

      {/* Blip dots (anomalies) */}
      {anomalyCount > 0 && (
        <>
          <motion.div
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
            className="absolute w-1.5 h-1.5 bg-nexus-red rounded-full"
            style={{ top: '25%', left: '60%' }}
          />
          {anomalyCount > 1 && (
            <motion.div
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 2, repeat: Infinity, delay: 1.2 }}
              className="absolute w-1 h-1 bg-nexus-orange rounded-full"
              style={{ top: '60%', left: '35%' }}
            />
          )}
        </>
      )}

      {/* Center dot */}
      <div className="w-2 h-2 bg-nexus-cyan rounded-full shadow-nexus-cyan z-10" />
    </div>
  )
}
