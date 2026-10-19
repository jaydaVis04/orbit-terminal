# MRROBOT wallpaper

Final asset: [assets/mrrobot.png](../assets/mrrobot.png).

Created with the built-in imagegen tool, with an opaque background. The generated
pixels are unchanged; textual PNG metadata was removed before packaging. The
installed copy lives at `~/.local/share/mrrobot/wallpaper.png`.

## Final generation prompt

```text
Use case: stylized-concept. Asset type: a finished cinematic ultrawide Kitty terminal wallpaper, landscape 16:9, 2560x1440 or highest available landscape resolution. Create a beautifully restrained Mr. Robot television show / fsociety themed terminal wallpaper in pure black, deep crimson red, and bone white. Composition is critical: the entire left 62 percent of the image must be almost-solid near black (#080608), with no text or high contrast shapes, so shell text remains readable. Place the complete artwork entirely in the rightmost 35 percent, with generous margins and nothing clipped: a striking fsociety Guy Fawkes mask in white and charcoal with a thin crimson rim glow, centered around x=82%, y=45%, and a small tasteful red angular 'MR. ROBOT' show-inspired wordmark beneath the mask, followed by smaller exact lowercase text 'fsociety' in white. The mask has recognizable arched brows, curled mustache, pointed beard, enigmatic grin, rendered as a sharp screenprint illustration with subtle weathered ink and very faint red scan lines confined to the artwork. Behind the mask a delicate crimson broken halo and sparse thin glitch fragments add depth, fading completely into the black negative space to the left. Premium hacker noir title-sequence design, minimalist, bold silhouette, elegant controlled grain, no rainbow/neon cyberpunk scenery, no desk, no computers, no people, no terminal interface or window mockup, no additional text, no watermark. Keep all words small relative to the mask and located on the far right, well within a 12% margin from the right edge. This is the wallpaper artwork itself, edge-to-edge, not a screenshot.
```

The reveal uses a transient dark graphics layer behind the terminal text. Kitty
receives the local background image once, then blends the cover away with a
smooth easing curve. Leaving restores Kitty's configured background image.

References: [Kitty background control](https://sw.kovidgoyal.net/kitty/remote-control/#kitten-set-background-image),
[Kitty graphics protocol](https://sw.kovidgoyal.net/kitty/graphics-protocol/).
