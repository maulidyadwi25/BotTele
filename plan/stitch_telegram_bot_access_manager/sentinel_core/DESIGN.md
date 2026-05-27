---
name: Sentinel Core
colors:
  surface: '#f9f9ff'
  surface-dim: '#d2daf0'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3ff'
  surface-container: '#e9edff'
  surface-container-high: '#e0e8ff'
  surface-container-highest: '#dbe2f9'
  on-surface: '#141b2c'
  on-surface-variant: '#434750'
  inverse-surface: '#293041'
  inverse-on-surface: '#edf0ff'
  outline: '#747781'
  outline-variant: '#c3c6d1'
  surface-tint: '#3c5e97'
  primary: '#002c5f'
  on-primary: '#ffffff'
  primary-container: '#1d437a'
  on-primary-container: '#90b1ef'
  inverse-primary: '#aac7ff'
  secondary: '#bc0100'
  on-secondary: '#ffffff'
  secondary-container: '#eb0000'
  on-secondary-container: '#fffbff'
  tertiary: '#2a2e30'
  on-tertiary: '#ffffff'
  tertiary-container: '#414447'
  on-tertiary-container: '#aeb1b4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d7e3ff'
  primary-fixed-dim: '#aac7ff'
  on-primary-fixed: '#001b3e'
  on-primary-fixed-variant: '#21467d'
  secondary-fixed: '#ffdad4'
  secondary-fixed-dim: '#ffb4a8'
  on-secondary-fixed: '#410000'
  on-secondary-fixed-variant: '#930100'
  tertiary-fixed: '#e0e3e6'
  tertiary-fixed-dim: '#c4c7ca'
  on-tertiary-fixed: '#191c1e'
  on-tertiary-fixed-variant: '#44474a'
  background: '#f9f9ff'
  on-background: '#141b2c'
  surface-variant: '#dbe2f9'
typography:
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-sm:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

This design system is built for an enterprise-grade File Access Management application, emphasizing security, authority, and industrial precision. The brand personality is vigilant and robust, designed to instill confidence in system administrators handling sensitive Telegram data assets.

The visual style is **Corporate / Modern** with a lean towards **Technical Minimalism**. It utilizes a clean light-mode interface by default to ensure maximum legibility, paired with high-contrast structural elements. The aesthetic avoids unnecessary flourishes, focusing instead on information density, clear hierarchies, and functional clarity to facilitate complex file management tasks.

## Colors

The palette is derived directly from the institutional heritage of the logo, optimized for digital interface utility.

*   **Primary (Security Blue):** A deep, authoritative navy used for primary actions, navigation headers, and active states. It represents stability and trust.
*   **Secondary (Alert Red):** A high-visibility red reserved strictly for destructive actions (Delete, Revoke Access), critical alerts, and brand-level accents.
*   **Neutral (Slate & Ink):** A range of cool grays and deep blacks used for text, borders, and subtle structural divisions.
*   **Surface:** A clean white background with off-white (`#F9FAFB`) container backgrounds to create subtle depth without relying on heavy shadows.

## Typography

The typography system prioritizes clarity and technical precision.

*   **Primary Typeface:** **Hanken Grotesk** is used for all primary UI text and headlines. Its sharp terminals and modern geometry provide an "engineering-first" look that feels reliable and contemporary.
*   **Secondary Typeface:** **Geist** is utilized for labels, metadata, and monospaced data (such as File IDs and Telegram Hashes). This ensures that technical strings are easily distinguishable from human-readable content.

Scale is used to manage high-density data views, with a focus on smaller, tighter line-heights for data tables to maximize the information visible on-screen.

## Layout & Spacing

The design system employs a **Fluid-Fixed Hybrid Grid**. The sidebar and navigation elements are fixed-width to maintain structural integrity, while the main content area (file browser and data tables) expands to fill the viewport.

*   **Grid:** A 12-column grid system is used for dashboard layouts.
*   **Spacing Rhythm:** An 8pt grid governs all component dimensions, while a 4pt grid handles internal component spacing (e.g., icon-to-text).
*   **Density:** Medium-high density is preferred. File rows and table cells should have compact padding to allow administrators to scan hundreds of entries efficiently.
*   **Breakpoints:**
    *   Mobile (< 768px): Single column, hidden sidebar (hamburger menu).
    *   Tablet (768px - 1280px): Collapsed sidebar (icons only), 8-column content.
    *   Desktop (> 1280px): Persistent sidebar, 12-column content.

## Elevation & Depth

This design system uses **Tonal Layering** and **Low-Contrast Outlines** rather than heavy shadows to convey depth, maintaining a crisp, flat-architectural feel.

*   **Level 0 (Background):** Pure white or `#F9FAFB`.
*   **Level 1 (Cards/Containers):** White background with a 1px border in `#EAECF0`.
*   **Level 2 (Active/Floating):** Used for dropdowns and context menus. Features a very soft, diffused shadow (`0px 4px 12px rgba(16, 24, 40, 0.08)`) and a sharp border.
*   **Interactive States:** Hovering over file rows or table entries triggers a subtle background shift to `#F2F4F7`.

## Shapes

To maintain the "Defend ID" industrial and secure aesthetic, shapes are kept disciplined and professional.

*   **Soft (0.25rem):** Standard for buttons, input fields, and small UI components.
*   **Large (0.5rem):** Used for cards, modals, and the file browser container.
*   **Pill (999px):** Used exclusively for status badges (e.g., "Active", "Encrypted", "Restricted") to provide a clear visual distinction from interactive buttons.

## Components

### Buttons
*   **Primary:** Solid `Security Blue` with white text. High-contrast, no gradient.
*   **Secondary:** White background with a `Security Blue` border.
*   **Destructive:** Outline or solid `Alert Red` for permanent file deletion or access revocation.

### Secure Login Form
*   Centered card layout with a heavy 1px border.
*   Fields feature prominent labels in `Geist` and clear focus states using a 2px `Security Blue` glow.
*   Includes specialized "Telegram Auth" buttons with distinctive iconography.

### Data Tables & File Browser
*   **Header:** Sticky headers with a subtle gray background and `label-md` typography.
*   **Multi-select:** A checkbox column on the far left. When multiple items are selected, a floating action bar appears at the bottom of the viewport with batch commands (Move, Delete, Export).
*   **File Icons:** Simplified, monochromatic icons to represent file types (PDF, Image, Video), changing to `Security Blue` when selected.

### Input Fields
*   Flat design with a light gray border.
*   Validation states use `Alert Red` for errors, accompanied by small helper text below the field.

### Chips & Badges
*   Small, low-profile badges for file tags or user permissions.
*   Background colors for badges should be very desaturated versions of the status color (e.g., light blue for "Admin", light red for "Suspended").