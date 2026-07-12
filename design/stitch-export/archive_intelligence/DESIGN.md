---
name: Archive Intelligence
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1c1b1b'
  on-surface-variant: '#43474f'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#747780'
  outline-variant: '#c4c6d0'
  surface-tint: '#405f91'
  primary: '#001736'
  on-primary: '#ffffff'
  primary-container: '#002b5b'
  on-primary-container: '#7594ca'
  inverse-primary: '#a9c7ff'
  secondary: '#635e56'
  on-secondary: '#ffffff'
  secondary-container: '#e6dfd4'
  on-secondary-container: '#67625a'
  tertiary: '#181812'
  on-tertiary: '#ffffff'
  tertiary-container: '#2d2c26'
  on-tertiary-container: '#96938b'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#a9c7ff'
  on-primary-fixed: '#001b3d'
  on-primary-fixed-variant: '#264778'
  secondary-fixed: '#e9e1d7'
  secondary-fixed-dim: '#cdc5bc'
  on-secondary-fixed: '#1e1b15'
  on-secondary-fixed-variant: '#4a463f'
  tertiary-fixed: '#e6e2d9'
  tertiary-fixed-dim: '#cac6be'
  on-tertiary-fixed: '#1c1c16'
  on-tertiary-fixed-variant: '#484740'
  background: '#fcf9f8'
  on-background: '#1c1b1b'
  surface-variant: '#e5e2e1'
typography:
  display-lg:
    fontFamily: Source Serif 4
    fontSize: 42px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Source Serif 4
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Source Serif 4
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '450'
    lineHeight: 18px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 1px
  stack-sm: 8px
  stack-md: 16px
  sidebar-width: 260px
---

## Brand & Style
The design system is built for Support Operations and Data Analysts who require high-velocity information processing without cognitive fatigue. The brand personality is "Quietly Confident" and "Intellectual," prioritizing utility over decoration. It draws inspiration from high-end editorial layouts and technical terminals to create a workspace that feels like a permanent tool rather than a fleeting app.

The style is a blend of **Minimalism** and **Modern Editorial**. It utilizes high-density information grids, precise hairline dividers, and a disciplined "paper-and-ink" aesthetic. The goal is to evoke the feeling of reading a well-typeset journal where data is the protagonist. 

**Core Principles:**
- **Clarity over Visual Noise:** Every pixel must serve a functional purpose.
- **Data Density:** Information is packed tightly but remains legible through superior typographic hierarchy.
- **Static Reliability:** No motion for motion's sake; transitions should be instant or highly functional.

## Colors
This design system uses a restricted, high-contrast palette to maintain focus. The primary background is a warm paper tone to reduce eye strain during long analytical sessions.

- **Background:** `#F9F7F2` (Warm Paper) acts as the base canvas.
- **Ink:** `#1A1A1A` (Near-Black) is used for all primary text and structural elements.
- **Accent:** `#002B5B` (Ink Blue) is the sole color used for primary actions, active states, and critical data highlights.
- **Muted/Borders:** `#E5E1D8` is used for all hairline strokes, dividers, and inactive UI borders.
- **Status:** Functional colors (Success/Warning/Error) should be desaturated to match the "Ink" aesthetic (e.g., a deep oxblood for errors rather than bright red).

## Typography
The typographic system pairs the authoritative, literary feel of **Source Serif 4** for headings with the surgical precision of **JetBrains Mono** for data points and **Hanken Grotesk** for interface controls.

- **Headlines:** Use Source Serif 4 for page titles and section headers to provide an editorial cadence.
- **Body:** Hanken Grotesk provides a modern, neutral contrast for descriptions and long-form notes.
- **Data & Metadata:** All timestamps, ticket IDs, metrics, and technical labels must use JetBrains Mono. This creates a clear visual distinction between "human narrative" and "machine data."

## Layout & Spacing
The layout follows a **Rigid Grid** philosophy. Content is organized into modular panes separated by 1px hairline borders rather than large gaps of whitespace.

- **Density:** Information density is high. Use 8px and 12px increments for internal component spacing to keep elements compact.
- **The Sidebar:** A fixed-width left navigation (`260px`) handles primary filtering, while a right-hand "Inspector" panel often appears for ticket details.
- **Tables:** Tables are the primary data vehicle. They should use a "No-Margin" approach where the cell content sits tight to the hairline borders, maximizing vertical visibility.
- **Responsiveness:** On smaller screens, the layout collapses into a single-column stack, prioritizing the "Data Mono" metadata at the top of each card.

## Elevation & Depth
This design system rejects shadows and 3D effects. Depth is conveyed entirely through **Tonal Layering** and **Line Work**.

- **Surfaces:** Use subtle shifts in background color to indicate depth. The main workspace is `#F9F7F2`, while sidebars or background layers can shift to a slightly cooler or warmer neutral to distinguish hierarchy.
- **Borders:** Hierarchy is created by stroke weight and color. 1px solid strokes in `#E5E1D8` are the primary way to define "containers."
- **Active State:** Selection is indicated by a solid 2px border of Ink Blue or a subtle background tint change. No "lifting" or floating effects are allowed.

## Shapes
The shape language is strictly **Sharp (0px)**. 

To maintain the professional, terminal-like aesthetic, avoid rounded corners on all functional elements including buttons, input fields, and cards. This reinforces the "Information Grid" concept where elements align perfectly to the pixel grid without the visual softening of radii. 

*Exception:* Only circular avatars for users are permitted to quickly distinguish human actors from data objects.

## Components
Consistent execution of these components is vital to the "Editorial" feel.

- **Buttons:** Rectangular with 1px borders. Primary buttons are solid Ink Blue with white text. Secondary buttons use a hairline border and JetBrains Mono text.
- **Data Tables:** High-density, 1px borders between rows and columns. Header cells use `label-caps` typography with a subtle background fill.
- **Input Fields:** Bottom-border only or full-framed with 1px strokes. Use JetBrains Mono for input text to signify data entry.
- **Chips/Badges:** Minimalist boxes with 1px borders. No fills unless indicating a specific status (e.g., a "Critical" tag might have a desaturated dark red background).
- **Tabs:** Simple underlined text or "Folder-style" boxes. The active tab is indicated by a solid top-stroke of the Accent color.
- **The "Command Bar":** A central, floating but sharp-edged search and action interface, utilizing the monospace font for all suggestions.