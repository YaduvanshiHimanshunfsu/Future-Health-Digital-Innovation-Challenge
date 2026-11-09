const TILES = ["#2F5BEA", "#14A89B", "#F4B740", "#E2725B", "#E58FA8", "#7A4FD6", "#7BAE4E", "#B9AEF7"];

/** A row of small glazed tiles between sections. Decorative: it settles in once, in a wave, then rests. */
export function MosaicDivider({ count = 24, className = "" }: { count?: number; className?: string }) {
  return (
    <div aria-hidden="true" className={`mosaic-divider ${className}`}>
      {Array.from({ length: count }, (_, index) => (
        <span
          key={index}
          style={{ backgroundColor: TILES[(index * 3) % TILES.length], animationDelay: `${index * 35}ms` }}
        />
      ))}
    </div>
  );
}
