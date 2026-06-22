interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
  id?: string;
}

export function Slider({ label, value, min, max, onChange, id }: SliderProps) {
  return (
    <div className="py-2">
      <div className="flex items-center justify-between mb-1.5">
        <label htmlFor={id} className="text-sm font-medium text-text-primary">
          {label}
        </label>
        <span className="text-sm font-semibold text-primary tabular-nums">{value}</span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-pill bg-slate-200 accent-primary cursor-pointer"
      />
      <div className="flex justify-between text-xs text-text-muted mt-1">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
