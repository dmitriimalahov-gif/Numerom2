# Living NumerOM identity

The existing transparent vector remains the source of truth. The components add a separate, transparent orbital scene; neither the canonical SVG nor generated assets are changed.

Design: preserve the mint ring (#B3DECC), add a dimensional mint planet (#7CCFB8), an ocean-blue satellite (#7A9FDF), and a smaller lilac satellite (#B7A2D7). Two additional palettes provide turquoise/lilac/gold and sage/blue/rose accents on replay. Typography stays inside the original vector. The original proportions and layout box stay fixed. Motion gives the orbit depth while the wordmark makes only a slight tilt, then returns to its exact original position.

A non-compact logo wakes for 4.4 seconds when it becomes visible on the website or mounts in the native application. Three planets travel in inclined orbits and the existing large planet acquires spherical shading. Everything settles back to the original artwork; no interval or infinite animation runs. Hover/touch, keyboard focus on a containing link, and a standalone replay button can repeat the web sequence. Interactions during playback do not restart it. Each replay advances the accent palette. A linked logo retains its existing navigation and never receives a nested button.

Compact artwork stays static. Web `prefers-reduced-motion` and native `AccessibilityInfo` preferences suppress motion and remove replay controls. A preference change stops current playback. Leaving the browser tab or backgrounding the native application also stops playback. Unmounting clears listeners, observers, timers, and native animations. Preferences default to static until known.

Web motion uses CSS transforms/opacity, and an IntersectionObserver avoids playing the introduction before an offscreen logo is seen. Native uses React Native Animated with the native driver and `isInteraction: false`. SVG artwork is memoized, and no SVG XML is changed or reparsed by animation frames. Neither implementation uses a network dependency or a canvas rasterization step.

Verification is recorded in the implementation handoff. The focused web tests cover settling, replay/palette changes, linked keyboard behavior, reduced motion, compact mode, offscreen introduction, and background/unmount cleanup. Native typechecking validates the strict TypeScript contracts; device animation still requires a simulator/device visual check.
