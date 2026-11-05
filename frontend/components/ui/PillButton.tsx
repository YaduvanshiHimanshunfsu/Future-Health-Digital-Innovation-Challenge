"use client";

import type { ButtonHTMLAttributes } from "react";

export function PillButton({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" }) {
  return <button type="button" className={`pill-${variant} ${className}`} {...props} />;
}
