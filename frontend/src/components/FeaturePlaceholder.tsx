interface FeaturePlaceholderProps {
  title: string;
  description: string;
  phase: string;
}

export function FeaturePlaceholder({
  title,
  description,
  phase,
}: FeaturePlaceholderProps): JSX.Element {
  return (
    <div>
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-500">{description}</p>
      </header>
      <div className="rounded-xl border border-dashed border-slate-300 bg-white/50 p-10 text-center">
        <p className="text-sm text-slate-500">This feature is delivered in {phase}.</p>
      </div>
    </div>
  );
}
