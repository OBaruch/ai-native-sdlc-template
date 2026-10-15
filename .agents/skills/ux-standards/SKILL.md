---
name: ux-standards
description: Apply the UX and accessibility standards. Use when designing or changing any user interface, flow, form, navigation, empty/error/loading state, or when producing a mock or screenshot for review.
---

# UX and accessibility standards

Owner: `<UX lead>` · Source of truth: `<link to the design system>` · Version: `<x.y>`

<!-- TEMPLATE: replace with your standards. -->

## Must
1. **Accessibility**: meet `<WCAG 2.2 AA>`: keyboard reachable, visible focus, labels on every
   input, contrast from design tokens, no information conveyed by colour alone.
2. **Components**: use `<design system package>` components; no bespoke replacements for
   existing ones.
3. **States**: every screen defines loading, empty, error and success states.
4. **Forms**: inline validation, errors next to the field, never clear user input on error.
5. **Responsive**: works from `<320px>` wide; no horizontal scrolling.
6. **Performance**: `<e.g. LCP < 2.5s on mid-range mobile>`.

## Verifying UI work
Screenshot the result at `<breakpoints>` and compare it with the approved mock. Iterate until
it matches; two or three rounds is normal.

## Output
In `spec.md`, list the flows and states affected. Conflicts with brand or compliance rules
go under **Areas of concern**, addressed to the owners involved.
