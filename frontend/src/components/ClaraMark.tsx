export type ClaraMarkState = "resting" | "working" | "done" | "correcting";

export function ClaraMark({ state = "resting", size = "md" }: { state?: ClaraMarkState; size?: "sm" | "md" | "lg" }) {
  const dimensions = { sm: "h-10 w-10", md: "h-16 w-16", lg: "h-28 w-28" }[size];
  return <svg className={`clara-mark clara-mark--${state} ${dimensions}`} viewBox="0 0 96 96" role="img" aria-label="Marca de Clara">
    <path className="clara-mark__body" d="M49 12c18 0 32 14 32 32 0 19-14 38-33 40C29 81 15 67 15 48c0-18 15-36 34-36Z" />
    <path className="clara-mark__thread" d="M29 51c8-17 18-23 34-18 7 2 11 7 12 13" fill="none" pathLength="1" />
    <circle className="clara-mark__seed" cx="55" cy="38" r="5" />
  </svg>;
}
