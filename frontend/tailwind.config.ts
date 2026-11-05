import type { Config } from "tailwindcss";

// Ceramic Chromatic, from the Stitch design system. See design-export/DESIGN.md.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  // Built at runtime from API values, such as `outcome-${key}`, so the scanner can't see them.
  safelist: [{ pattern: /^outcome-(two_copies|carrier|neither|other)$/ }, { pattern: /^glaze-[1-4]$/ }],
  theme: {
    extend: {
      colors: {
        porcelain: "#FBF8F3",
        glaze: "#FFFFFF",
        line: "#E6DED2",
        sand: { DEFAULT: "#E9DFCF", light: "#F3EDE4" },
        ink: "#1F2433",
        slate: "#5B6275",
        lapis: { DEFAULT: "#2F5BEA", dark: "#2448C4", tint: "#EDF1FE" },
        // Fills carry ink text. The deep versions are for text on light backgrounds.
        turquoise: { DEFAULT: "#14A89B", deep: "#0E776E", tint: "#E3F6F4" },
        plum: { DEFAULT: "#7A4FD6", deep: "#5F31BA", tint: "#F0EBFB" },
        saffron: { DEFAULT: "#F4B740", deep: "#866523", tint: "#FDF4E0" },
        terracotta: { DEFAULT: "#E2725B", deep: "#A55342", tint: "#FBEDE9" },
        lilac: "#B9AEF7",
      },
      fontFamily: {
        display: ["var(--font-display)", "var(--font-devanagari)", "system-ui", "sans-serif"],
        body: ["var(--font-body)", "var(--font-devanagari)", "system-ui", "sans-serif"],
      },
      borderRadius: { plate: "24px", field: "16px", chip: "12px" },
      boxShadow: {
        clay: "inset 0 1.5px 0 0 rgba(255,255,255,.95), 0 4px 16px -2px rgba(91,98,117,.06), 0 1px 3px 0 rgba(91,98,117,.04)",
        float: "inset 0 1.5px 0 0 rgba(255,255,255,1), 0 10px 24px -4px rgba(31,36,51,.08), 0 2px 6px -1px rgba(31,36,51,.04)",
        pill: "inset 0 1px 0 rgba(255,255,255,.3), 0 6px 14px -4px rgba(47,91,234,.35)",
      },
      maxWidth: { page: "1200px" },
      keyframes: {
        rise: { from: { opacity: "0", transform: "translateY(10px)" }, to: { opacity: "1", transform: "none" } },
        pop: { from: { opacity: "0", transform: "scale(.6)" }, to: { opacity: "1", transform: "none" } },
      },
      animation: { rise: "rise .5s cubic-bezier(.2,.7,.2,1) both", pop: "pop .3s ease-out both" },
    },
  },
  plugins: [],
};

export default config;
