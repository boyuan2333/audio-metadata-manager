---
name: Dark Stone
colors:
  surface: '#121416'
  surface-dim: '#121416'
  surface-bright: '#38393c'
  surface-container-lowest: '#0c0e10'
  surface-container-low: '#1a1c1e'
  surface-container: '#1e2022'
  surface-container-high: '#282a2c'
  surface-container-highest: '#333537'
  on-surface: '#e2e2e5'
  on-surface-variant: '#c5c6ca'
  inverse-surface: '#e2e2e5'
  inverse-on-surface: '#2f3133'
  outline: '#8f9194'
  outline-variant: '#44474a'
  surface-tint: '#c3c7cd'
  primary: '#eef1f7'
  on-primary: '#2c3136'
  primary-container: '#d1d5db'
  on-primary-container: '#585c61'
  inverse-primary: '#5a5f64'
  secondary: '#bdc7d8'
  on-secondary: '#27313e'
  secondary-container: '#404a57'
  on-secondary-container: '#afb9c9'
  tertiary: '#ebf1ff'
  on-tertiary: '#273140'
  tertiary-container: '#cbd5e9'
  on-tertiary-container: '#525c6d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dfe3e9'
  primary-fixed-dim: '#c3c7cd'
  on-primary-fixed: '#171c20'
  on-primary-fixed-variant: '#43474c'
  secondary-fixed: '#d9e3f4'
  secondary-fixed-dim: '#bdc7d8'
  on-secondary-fixed: '#121c28'
  on-secondary-fixed-variant: '#3e4755'
  tertiary-fixed: '#d9e3f7'
  tertiary-fixed-dim: '#bdc7db'
  on-tertiary-fixed: '#121c2a'
  on-tertiary-fixed-variant: '#3d4757'
  background: '#121416'
  on-background: '#e2e2e5'
  surface-variant: '#333537'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 24px
  margin: 32px
  container-max: 1280px
---

## Brand & Style
The brand personality is architectural, disciplined, and high-performance. It is designed for professional environments where focus and visual endurance are paramount. The "Dark Stone" aesthetic shifts away from the starkness of pure black toward a naturally occurring obsidian and charcoal palette, maintaining a warm, geological undertone.

The design style is **Corporate Modern with a Minimalist lean**, emphasizing "studio feel" through high information density, intentional whitespace, and a sophisticated layering system. It evokes an emotional response of quiet confidence and technical precision, suitable for high-end SaaS, engineering tools, or creative studios.

## Colors
The palette is rooted in deep, matte minerals. The foundation is **Obsidian (#121416)**, used for the primary canvas to reduce eye strain and provide a grounding depth. Surfaces and containers use **Charcoal (#1A1C1E)** to create a subtle lift.

Text hierarchies are strictly enforced:
- **Primary Text:** Off-white (#F9FAFB) for maximum readability without the "vibration" of pure white.
- **Secondary/Supporting Text:** Light Gray (#9CA3AF) for metadata and labels.
- **Accents:** Muted silver and stone tones are used for interactive states, keeping the interface monochromatic and professional.

## Typography
This design system utilizes **Inter** exclusively to achieve a systematic, utilitarian aesthetic. The type scale is tight, favoring legibility in dense data environments. 

Headlines use semi-bold weights with negative letter-spacing to create a "compacted" professional look. Body text prioritizes a generous line-height to maintain breathability against the dark background. Labels are often treated with a slight tracking increase and uppercase transform to distinguish them as functional UI elements rather than narrative content.

## Layout & Spacing
The system follows a **12-column fluid grid** for desktop, transitioning to a **4-column grid** for mobile. A strict 4px base-unit ensures that all components and layouts remain mathematically aligned.

- **Desktop:** 32px outer margins with 24px gutters.
- **Tablet:** 24px outer margins with 16px gutters.
- **Mobile:** 16px outer margins with 12px gutters.

The layout philosophy centers on "Professional Density"—minimizing excessive padding to allow more information on screen while using grouped margins to define content blocks.

## Elevation & Depth
In this dark environment, depth is communicated through **Tonal Layers** and **Subtle Borders** rather than aggressive shadows. 

1.  **Level 0 (Base):** Obsidian (#121416).
2.  **Level 1 (Surface):** Charcoal (#1A1C1E) with a 1px solid border (#2D2F31).
3.  **Level 2 (Popovers/Modals):** Lighter Charcoal (#242628) with a soft, 15% opacity black shadow (0px 8px 24px).

Borders are essential to the "studio" aesthetic; they define the skeleton of the UI. Use a low-contrast border color (#2D2F31) for all container edges to provide structure without creating visual noise.

## Shapes
The shape language is controlled and sophisticated, utilizing the **Rounded (0.5rem)** standard. 

- **Standard Components:** 8px (0.5rem) radius for buttons, inputs, and small cards.
- **Large Containers:** 16px (1rem) radius for main content areas and modals.
- **Interactive States:** Subtle scale-down (98%) on press to simulate physical tactility within a digital environment.

## Components
- **Buttons:** Primary buttons use the light-gray scale (#D1D5DB) with dark text (#121416) for immediate hierarchy. Secondary buttons are outlined with #2D2F31 borders and light gray text.
- **Input Fields:** Background matches the base layer (#121416) but features a 1px border. Focus states use a primary stone-gray border with a subtle 2px outer glow.
- **Cards:** Use the Level 1 Surface (#1A1C1E). Padding should be a consistent 24px (lg spacing) to maintain the premium feel.
- **Chips:** Small, low-profile elements with a 4px radius. Use #2D2F31 backgrounds with #9CA3AF text.
- **Lists:** Rows are separated by 1px horizontal lines (#2D2F31). Hover states for list items should use a subtle background shift to #242628.
- **Checkboxes/Radios:** Square-ish with the 4px radius, maintaining the architectural theme. Selected states use the high-contrast light gray.