---
version: alpha
name: DRSK Interface System
description: The approved DRSK homepage language adapted from cinematic brand expression to operational and research workspaces.
colors:
  bg-canvas: "#000000"
  bg-surface: "#111113"
  bg-subtle: "#19191c"
  text-primary: "#ffffff"
  text-secondary: "#c8c8c8"
  text-tertiary: "#8e8e8e"
  border-subtle: "rgba(255, 255, 255, 0.12)"
  border-strong: "rgba(255, 255, 255, 0.24)"
  drsk-accent: "#ffffff"
  sourcechain-accent: "#8ab8ff"
  niyet-accent: "#f0ae78"
  status-support: "#79d6b2"
  status-caution: "#efc36d"
  status-conflict: "#ef929c"
typography:
  sans:
    fontFamily: Inter, Segoe UI, system-ui, sans-serif
  display:
    fontFamily: BubbledotICG-FinePos, Geist Pixel Circle, monospace
  mono:
    fontFamily: Geist Pixel Circle, Consolas, monospace
rounded:
  sm: 10px
  md: 16px
  lg: 24px
---

## Overview

DRSK is an evidence-aware social coordination product. Its approved interface is black, high-contrast, minimal, futuristic, and editorial. The homepage is the cinematic expression; Feed, SOURCECHAIN, NIYET, and Allocation Lab are functional expressions of the same identity.

## Colors

Use the black canvas as the dominant field. Operational hierarchy comes from lightness separation between canvas, surfaces, and fine translucent borders, not from large tinted panels. SOURCECHAIN blue and NIYET warm amber are semantic accents; neither replaces the monochrome DRSK foundation. Status meaning always includes text or an icon in addition to color.

## Typography

Inter is the default for interface copy, forms, navigation, and dense reading. Bubbledot with Geist Pixel fallback is reserved for brand display, page identity, technical labels, and selected metrics. Never set paragraphs, long explanations, or form values in the display face.

## Layout

The homepage remains a single full-bleed viewport. Product workspaces use a centered shell beneath universal navigation, with restrained page padding, clear section rhythm, and denser layouts where evidence or allocation data require it. Mobile reorganizes content instead of scaling desktop columns down.

## Elevation & Depth

Depth comes from translucent dark surfaces, fine borders, restrained blur, and sparse shadows. Avoid stacked bright cards, heavy glow, and decorative gradients behind dense content.

## Shapes

Primary actions and navigation use pills. Icon controls are circular. Sheets and major workspace surfaces use the large radius; dense evidence rows and controls use the small or medium radius. Radius communicates component role and must not be maximized indiscriminately.

## Components

Universal navigation uses the circular DRSK mark, white navigation pill, dark secondary action, three-dot active marker, EN/TR control, and circular mobile burger. Buttons share pill geometry, visible focus, and clear primary, secondary, ghost, danger, and icon roles. Inputs use dark surfaces, readable placeholders, fine borders, and a high-contrast focus ring. Dialogs and drawers use a dark scrim, blur, and a bordered dark sheet.

## Do's and Don'ts

Preserve the homepage video and art direction. Propagate its language rather than its hero composition. Keep analytical SOURCECHAIN surfaces calm and precise, give NIYET a restrained warmer accent, and let Lab remain dense. Do not reintroduce white application canvases, Bootstrap-like rectangular buttons, raw internal enums, decorative dashboard gradients, or paragraphs in dot-matrix typography.
