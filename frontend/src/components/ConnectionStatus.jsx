export default function ConnectionStatus({ status }) {
  const cfg = {
    connected:    { color: "#00FF88", glow: "0 0 8px #00FF8880", text: "BAĞLI" },
    connecting:   { color: "#FFAA00", glow: "0 0 8px #FFAA0080", text: "BAĞLANIYOR" },
    disconnected: { color: "#FF3366", glow: "0 0 8px #FF336680", text: "BAĞLANTI_KESİK" },
  };
  const c = cfg[status] || cfg.disconnected;

  return (
    <div className="flex items-center gap-2">
      <span className="w-2 h-2 rounded-full" style={{ background: c.color, boxShadow: c.glow }} />
      <span className="text-xs font-bold uppercase tracking-wider" style={{
        color: c.color,
        textShadow: `0 0 8px ${c.color}40`,
      }}>{c.text}</span>
    </div>
  );
}
