import Link from "next/link";

/**
 * A lock chip that leads to the privacy centre. It names a place, not a promise: what is shared, with
 * whom and until when is shown there, so the badge itself claims nothing.
 */
export function PrivacyBadge({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="chip min-h-11 border-turquoise/40 bg-turquoise-tint text-turquoise-deep hover:border-turquoise">
      <svg viewBox="0 0 16 16" aria-hidden="true" className="h-3.5 w-3.5">
        <path d="M4.5 7V5a3.5 3.5 0 0 1 7 0v2" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <rect x="3" y="7" width="10" height="7" rx="2" fill="currentColor" />
      </svg>
      {label}
    </Link>
  );
}
