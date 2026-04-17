export function Input({
  label,
  type = "text",
  placeholder,
  value,
  onChange
}: {
  label: string;
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="text-white/70">{label}</span>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-white placeholder:text-white/30 outline-none focus:ring-2 focus:ring-white/10"
      />
    </label>
  );
}

export function Textarea({
  label,
  placeholder,
  value,
  onChange
}: {
  label: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="text-white/70">{label}</span>
      <textarea
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={5}
        className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-white placeholder:text-white/30 outline-none focus:ring-2 focus:ring-white/10"
      />
    </label>
  );
}
