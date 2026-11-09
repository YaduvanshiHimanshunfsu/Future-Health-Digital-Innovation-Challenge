"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";

/**
 * A glazed tile with a question on the front and its answer on the back.
 *
 * The server renders the question and answer together, so the answer is never locked behind script.
 * Once the page runs, the tile flips on a real button. Both sides carry the question as their heading,
 * and the hidden side is inert, so keyboard and screen reader only ever meet the side that is showing.
 * With reduced motion it fades instead of turning.
 */
export function TileFlip({
  title,
  answer,
  showLabel,
  hideLabel,
  accent = 1,
}: {
  title: string;
  answer: ReactNode;
  showLabel: string;
  hideLabel: string;
  accent?: 1 | 2 | 3 | 4;
}) {
  const [interactive, setInteractive] = useState(false);
  const [flipped, setFlipped] = useState(false);
  const backId = useId();
  const showButton = useRef<HTMLButtonElement>(null);
  const hideButton = useRef<HTMLButtonElement>(null);
  const moved = useRef(false);
  useEffect(() => setInteractive(true), []);
  // The pressed button goes inert with its side, so focus follows to the side now showing.
  useEffect(() => {
    if (!moved.current) return;
    (flipped ? hideButton : showButton).current?.focus();
  }, [flipped]);
  const turn = (to: boolean) => {
    moved.current = true;
    setFlipped(to);
  };
  const heading = <h2 className="text-xl font-medium">{title}</h2>;

  if (!interactive) {
    return (
      <div className={`plate glaze-edge glaze-${accent} grid gap-3`}>
        {heading}
        {answer}
      </div>
    );
  }
  return (
    <div className="tile-flip" data-flipped={flipped}>
      <div className="tile-flip-inner">
        <div className={`tile-face plate glaze-edge glaze-${accent}`} inert={flipped}>
          {heading}
          <button ref={showButton} type="button" className="pill-secondary mt-auto" aria-expanded={false} aria-controls={backId} onClick={() => turn(true)}>
            {showLabel}
          </button>
        </div>
        <div id={backId} className={`tile-face tile-back plate glaze-edge glaze-${accent}`} inert={!flipped}>
          {heading}
          {answer}
          <button ref={hideButton} type="button" className="pill-secondary mt-auto" aria-expanded={true} aria-controls={backId} onClick={() => turn(false)}>
            {hideLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
