import type { Config } from "tailwindcss";

const colour = (name: string) => `var(--${name})`;

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: Object.fromEntries(
        [
          "porcelain", "glaze", "sand", "line", "ink", "slate",
          "lapis", "plum", "turquoise", "terracotta", "saffron", "rose-clay", "olive", "lilac",
          "lapis-text", "plum-text", "turquoise-text", "terracotta-text",
          "saffron-text", "rose-clay-text", "olive-text",
          "risk-two-copies", "risk-carrier", "risk-neither",
        ].map((name) => [name, colour(name)]),
      ),
      borderRadius: {
        tile: "var(--radius-tile)",
        input: "var(--radius-input)",
        chip: "var(--radius-chip)",
      },
      boxShadow: {
        clay: "var(--shadow-clay)",
        "clay-pressed": "var(--shadow-clay-pressed)",
      },
      transitionTimingFunction: {
        settle: "var(--ease-settle)",
      },
    },
  },
} satisfies Config;
