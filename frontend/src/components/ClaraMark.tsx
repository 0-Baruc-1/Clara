export type ClaraMarkState = "resting" | "working" | "done" | "correcting";

/** Original vector mascot; state styling is driven solely by the existing agent flow. */
export function ClaraMark({ state = "resting", size = "md" }: { state?: ClaraMarkState; size?: "sm" | "md" | "lg" }) {
  const dimensions = { sm: "h-11 w-11", md: "h-20 w-20", lg: "h-36 w-36" }[size];
  return <svg className={`clara-mark clara-mark--${state} ${dimensions}`} viewBox="0 0 120 130" role="img" aria-label={`Clara: ${state}`}>
    <g className="clara-mark__sprout" stroke="#075b50" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="#0c7563">
      <path d="M60 25V14" fill="none" /><path d="M59 15C47 13 43 5 45 2c10 0 15 6 14 13Z" /><path d="M61 15c2-9 8-13 16-12 1 8-5 14-16 12Z" />
    </g>
    <path className="clara-mark__body" d="M61 23c25 0 35 18 39 37 3 13 17 22 13 40-2 11-11 19-23 21 2 6 5 10 1 12-6 2-11-1-13-8H43c-3 7-8 10-14 8-4-2-1-7 1-12C18 119 9 111 7 100c-4-18 10-28 14-42 6-20 15-35 40-35Z" />
    <ellipse className="clara-mark__face" cx="60" cy="59" rx="31" ry="25" />
    <g className="clara-mark__neutral clara-mark__expression" stroke="#075b50" strokeWidth="4" strokeLinecap="round" fill="none"><ellipse cx="49" cy="57" rx="2.4" ry="4.2" fill="#075b50" /><ellipse cx="71" cy="57" rx="2.4" ry="4.2" fill="#075b50" /><path d="M53 68c4 4 9 4 14 0" /></g>
    <g className="clara-mark__focused clara-mark__expression" stroke="#075b50" strokeWidth="4" strokeLinecap="round" fill="none"><path d="M44 52h9M67 52h9" /><ellipse cx="49" cy="59" rx="2.3" ry="4" fill="#075b50" /><ellipse cx="71" cy="59" rx="2.3" ry="4" fill="#075b50" /><path d="M55 69c3 2 7 2 10 0" /></g>
    <g className="clara-mark__pleased clara-mark__expression" stroke="#075b50" strokeWidth="4" strokeLinecap="round" fill="none"><path d="M43 59c3-6 9-6 12 0M65 59c3-6 9-6 12 0M53 68c4 5 10 5 14 0" /></g>
    <g className="clara-mark__surprised clara-mark__expression" stroke="#075b50" strokeWidth="4" strokeLinecap="round" fill="none"><ellipse cx="49" cy="58" rx="2.5" ry="4.5" fill="#075b50" /><ellipse cx="71" cy="58" rx="2.5" ry="4.5" fill="#075b50" /><circle cx="60" cy="70" r="3.5" /></g>
    <g className="clara-mark__arms" stroke="#075b50" strokeWidth="5" strokeLinecap="round" fill="none"><path d="M30 84c-9 8-8 16 3 19 7 2 12-2 15-8" /><path d="M90 82c9 8 8 16-3 19-7 2-12-2-15-8" /></g>
    <g className="clara-mark__tools" stroke="#075b50" strokeWidth="4" strokeLinejoin="round"><path className="clara-mark__notebook" d="M68 78l23-5 5 31-24 5Z" fill="#fffdf6" /><path d="M72 82l16-3" fill="none" stroke="#e8ad79" strokeWidth="2" /><path className="clara-mark__pencil" d="M34 79l7-4 13 25-7 4Z" fill="#e49a3d" /><path d="M34 79l-2-6 5 2Z" fill="#fff4dc" /></g>
    <g className="clara-mark__alerts" stroke="#e9872f" strokeWidth="4" strokeLinecap="round"><path d="M99 39l5-8M105 46l9-3M103 54l9 2" /></g>
  </svg>;
}
