import { PathDraw } from "@/components/motion/PathDraw";

/** A decorative picture of two parents and a child. It shows no result and no real data. */
export function InheritanceArt() {
  return (
    <svg viewBox="0 0 320 240" aria-hidden="true" className="w-full">
      <defs>
        <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="6" height="6" fill="#7A4FD6" />
          <rect width="2" height="6" fill="#fff" fillOpacity=".4" />
        </pattern>
      </defs>
      <PathDraw d="M70 60C70 130 160 110 160 180" fill="none" stroke="#B9AEF7" strokeWidth="4" strokeLinecap="round" />
      <PathDraw d="M250 60C250 130 160 110 160 180" fill="none" stroke="#B9AEF7" strokeWidth="4" strokeLinecap="round" />
      {[[50, 50, "#14A89B"], [90, 50, "#E9DFCF"], [230, 50, "#14A89B"], [270, 50, "#E9DFCF"]].map(([x, y, fill]) => (
        <circle key={`${x}`} cx={x as number} cy={y as number} r="18" fill={fill as string} stroke="#fff" strokeWidth="3" />
      ))}
      <circle className="icon-settle" style={{ animationDelay: ".5s" }} cx="140" cy="190" r="18" fill="#14A89B" stroke="#fff" strokeWidth="3" />
      <circle className="icon-settle" style={{ animationDelay: ".65s" }} cx="180" cy="190" r="18" fill="#E9DFCF" stroke="#fff" strokeWidth="3" />
    </svg>
  );
}
