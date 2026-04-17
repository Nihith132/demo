export function Card({
  title,
  desc,
  children
}: {
  title: string;
  desc?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold">{title}</h2>
          {desc ? <p className="mt-1 text-sm text-white/70">{desc}</p> : null}
        </div>
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}
