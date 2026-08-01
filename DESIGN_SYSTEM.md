# Design System

## Personality

Modern, friendly, bubbly, rounded, spacious, polished — professional enough for money.

## Color tokens (CSS variables)

Primary theme: ocean/teal — **not purple**.

```css
--background: warm off-white
--foreground: deep navy / charcoal
--primary: ocean blue / teal
--success: mint green
--warning: coral
--pending: warm amber
--destructive: controlled red
--card / --muted / --border: layered neutrals
```

Dark mode uses deep navy surfaces with high-contrast text and muted status colors. No purple tint.

## Shape

- Inputs/small cards: 12–16px radius
- Major cards/panels/modals: 18–24px
- Filters/status: fully rounded pills
- Soft shadows, subtle borders, generous whitespace

## Typography

Modern readable sans (Plus Jakarta Sans / Source Sans). Tabular nums for money. Clear hierarchy; large controlled dashboard totals; compact readable tables.

## Motion

Subtle loading, import progress, panel expand, status change, chart transitions. Respect `prefers-reduced-motion`.

## Components

shadcn/ui primitives restyled with tokens. Status badges always include text labels (not color alone). Charts include textual summaries for accessibility.

## Anti-patterns

- Purple-dominant themes
- Harsh square enterprise chrome
- Hardcoded chart/transaction values in components
- Cards used only for decoration when not needed for interaction grouping in dense financial tables (tables may sit in soft panels)
