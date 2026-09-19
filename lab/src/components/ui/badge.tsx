import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "steel" | "forest" | "rust" | "amber";

const tones: Record<Tone, string> = {
  neutral: "bg-elevated text-muted border-line",
  steel: "bg-steel/15 text-steel border-steel/30",
  forest: "bg-forest/20 text-forest-fg border-forest/40",
  rust: "bg-rust/20 text-rust-fg border-rust/40",
  amber: "bg-amber/15 text-fg border-amber/30",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-wide",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
