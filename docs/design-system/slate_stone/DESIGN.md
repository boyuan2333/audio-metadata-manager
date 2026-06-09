---
name: Slate & Stone
colors:
  surface: '#fbf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f3'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#46464b'
  inverse-surface: '#303030'
  inverse-on-surface: '#f3f0f0'
  outline: '#76777c'
  outline-variant: '#c6c6cc'
  surface-tint: '#5a5e6a'
  primary: '#1b1f29'
  on-primary: '#ffffff'
  primary-container: '#30343f'
  on-primary-container: '#999ca9'
  inverse-primary: '#c3c6d3'
  secondary: '#5d5e63'
  on-secondary: '#ffffff'
  secondary-container: '#dfdfe5'
  on-secondary-container: '#616267'
  tertiary: '#261e0f'
  on-tertiary: '#ffffff'
  tertiary-container: '#3c3322'
  on-tertiary-container: '#a89b85'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dfe2f0'
  primary-fixed-dim: '#c3c6d3'
  on-primary-fixed: '#171c25'
  on-primary-fixed-variant: '#424752'
  secondary-fixed: '#e2e2e7'
  secondary-fixed-dim: '#c6c6cb'
  on-secondary-fixed: '#1a1c20'
  on-secondary-fixed-variant: '#45474b'
  tertiary-fixed: '#f0e0c8'
  tertiary-fixed-dim: '#d3c5ad'
  on-tertiary-fixed: '#221b0b'
  on-tertiary-fixed-variant: '#4f4533'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.5px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin: 24px
---

# Slate & Stone Design System

## Brand & Style
The brand identity has shifted from a vibrant, energetic orange to a sophisticated, grounded, and professional aesthetic. The personality is "Modern Corporate" with a hint of "Minimalism." It evokes feelings of stability, precision, and architectural balance. The target audience includes professionals who value clarity and a focused, low-distraction environment. The UI uses a muted, cool-toned palette to create a calm and productive atmosphere.

## Colors
The color palette is anchored by Slate Gray and Stone tones.
- **Primary (#737783):** A balanced slate gray used for key action points and primary branding.
- **Secondary (#76777c):** A neutral gray that supports the primary color in less dominant UI elements.
- **Tertiary (#3c3322):** A deep, dark earth tone used for subtle contrast or specialized accents.
- **Neutral (#787777):** A mid-tone gray used for borders, icons, and secondary text to maintain a cohesive, low-vibrancy look.

The system operates in a light mode with high-clarity backgrounds and subtle monochromatic layering.

## Typography
The system uses **Inter** for all text roles, ensuring maximum readability and a clean, Swiss-inspired appearance.
- **Headlines:** Use semi-bold weights for clear hierarchy without being overly aggressive.
- **Body Text:** Optimized for legibility with generous line heights.
- **Labels:** Slightly tracked out for better recognition at small sizes.

## Layout & Spacing
The layout follows a fluid grid system with a steady 8px spacing rhythm. Content is organized with clear margins (24px) and gutters (16px). The philosophy focuses on "Negative Space" to separate concerns rather than heavy lines, allowing the monochromatic color palette to breathe.

## Elevation & Depth
Visual hierarchy is achieved through **Tonal Layers** and **Low-Contrast Outlines**. Instead of heavy shadows, the system uses subtle shifts in surface grays to indicate depth. Where elevation is necessary (e.g., modals), an extra-diffused, low-opacity neutral shadow is used to provide a soft "lift" from the background.

## Shapes
The shape language is **Rounded**. Standard components feature a 0.5rem (8px) corner radius, creating a softer, more approachable feel that balances the professional color palette. Larger containers like cards may use `rounded-lg` (16px) to emphasize structure.

## Components
- **Buttons:** Use the Primary Slate color with white text. Rounded corners (8px) and no shadows. Hover states should slightly darken the slate fill.
- **Input Fields:** Utilize a 1px neutral border with a subtle gray background. Focus states use the primary slate color for the border.
- **Cards:** Defined by low-contrast outlines or a very slight tonal shift from the background to maintain the minimalist feel.
- **Chips:** Highly rounded (pill-shaped) with a secondary gray fill and medium-weight labels.
- **Lists:** Clean separators using the Neutral tone at low opacity to guide the eye without adding clutter.