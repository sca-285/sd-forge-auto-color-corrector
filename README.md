# Stable Diffusion Forge: Auto Color Corrector

Fixes what is off in every generated image, and nothing else: JPEG blocking,
noise, colour casts, milky blacks, a frame that is too dark or too bright, flat
or harsh contrast, dull colour, and (when ticked) a tilted horizon. Each fix measures the image first and is skipped when there is
nothing to fix, so a well-made image comes through untouched. Works on Forge,
reForge and Forge Classic (Neo). No models, no downloads: it reads the
picture's own histogram and colours.

![Before / after](reference.jpg)

## Where it fits

Three extensions split the work the way a photo is made, and run in this
order:

| 1. [Auto Color Corrector](https://github.com/sca-285/sd-forge-auto-color-corrector) | 2. [Optical Realism](https://github.com/sca-285/sd-forge-optical-realism) | 3. [Digital Mastering](https://github.com/sca-285/sd-webui-digital-mastering) |
|---|---|---|
| **Correction**, automatic: measures the image and fixes only what is off (colour cast, black and white points, exposure, flat or harsh contrast, dull colour, JPEG blocks, noise, a tilted horizon), or matches a reference picture | **The camera**: lens geometry, vignette, purple fringing, depth of field and bokeh, tilt-shift, blur, bloom, flare, anamorphic streak, star filter, god rays, halation, light wrap, flash, haze, grain, dust, scratches, date stamp, highlight roll-off, retro video | **The grade**, by hand or by preset: exposure, contrast, white balance, saturation, vibrance, split toning, CDL, LUT, selective colour, clarity, sharpen, overlays, HSL, colour wheels, tone curves, black & white, dehaze, skin smoothing, local light, subtitles, anti-banding |

No two of them do the same job. Auto Color Corrector and Digital Mastering
both touch exposure and white balance, but for opposite ends: the corrector
brings a faulty picture back to neutral by itself and leaves a sound one
alone; Digital Mastering moves a picture away from neutral, on purpose, by
the amount you set. Correct first, then shoot, then grade.

A grade laid on a picture with a green cast or crushed blacks carries the
fault along; correcting first gives the other two a clean start. Nothing
here is a look: for looks, use the presets of the other two.

## Combining presets

Each extension's presets cover only its own side, so a finished look is one
preset from each, in the order they run: Auto Color Corrector cleans up, Optical
Realism adds the camera, Digital Mastering grades. Leave out any of the three
you do not need.

### Recipes

Complete looks, from the first extension to the last.

| Look | Auto Color Corrector | Optical Realism | Digital Mastering |
|---|---|---|---|
| Clean commercial portrait | Natural | Portrait 85mm f/1.8 | Portrait: Studio Skin |
| Fashion editorial | Natural | Retro Glass | Portrait: Editorial Crisp |
| Bridal, dreamy | Gentle | Portrait f/1.2 Dreamy | Portrait: Soft Glamour |
| Backlit at golden hour | Keep the Mood | Backlit Rim Light | Mood: Golden Hour |
| Contemporary film portrait | Natural | Retro Glass Deep | Film: Portra Golden |
| 35 mm travel snapshot | Natural | Film Camera 35mm | Film: Travel Ektar |
| Sixties holiday slide | Natural | Street 35mm f/5.6 | Film: Kodachrome |
| Hong Kong neon night | Keep the Mood | Night City Glow | Auteur: Chungking Neon |
| Lamp-lit interior, romance | Keep the Mood | Pro-Mist Cinema | Auteur: Mood for Love |
| Rainy city at night | Keep the Mood | Anamorphic Night | Auteur: Saigon Rain |
| Summer blockbuster | Standard | Anamorphic Flare | Cinema: Blockbuster |
| Neo-noir detective | Keep the Mood | Dusty Night Film | Cinema: Neo-Noir Blue |
| Classic black & white | Standard | Heavy Film Grain | B&W: Classic Silver |
| Mountain landscape | Standard | Landscape Aerial Haze | Film: Velvia |
| Misty northern coast | Keep the Mood | Foggy Morning | Auteur: Nordic Noir |
| Day for night | Natural | Subtle Real Camera | Cinema: Day for Night |
| House party | Natural | Digital Flash | Mood: Flash Snapshot |
| Nineties home video | Repair Only | VHS Home Video | Film: Instant Photo |
| Cyberpunk street | Keep the Mood | Hexagon Night Bokeh | Mood: Cyberpunk Neon |
| Toy town from above | Standard | Miniature World | Mood: Anime Vivid |
| Old photo brought back | Old Photo Scan | Vintage Lens | B&W: Sepia |
| Light in the nave | Keep the Mood | Cathedral Light | Film: Tungsten Amber |
| Christmas lights | Keep the Mood | Star Filter Night | Auteur: Happy Together |
| Garden storybook portrait | Gentle | Swirly Vintage Portrait | Auteur: Pastel Symmetry |
| Nature up close | Standard | Macro Close-up | Natural: HDR Detail |
| Digital breakdown | Repair Only | Glitch Art | Splash: Neon Blue |

### Partners for every camera

Every Optical Realism preset with the Digital Mastering looks that suit it
(the first one is the closest match) and the correction to run first. Every
Digital Mastering preset appears at least once.

| Optical Realism | Digital Mastering | Auto Color Corrector |
|---|---|---|
| Subtle Real Camera | Natural: Clean Polish · Natural: Crisp Clear · Film: Travel Ektar · Cinema: Day for Night | Natural |
| Portrait 85mm f/1.8 | Portrait: Studio Skin · Portrait: Golden Skin · Film: Portra Golden · Splash: Subject in Colour | Natural |
| Portrait f/1.2 Dreamy | Portrait: Soft Glamour · Mood: Lavender Dusk · Auteur: Pastel Symmetry · Film: Portra Golden | Gentle |
| Street 35mm f/5.6 | Natural: Vivid Pop · Film: Kodachrome · Auteur: Matte Street · Film: Cool Slide Stock · Splash: Golden Yellow · Splash: Red Accent | Standard |
| Macro Close-up | Natural: HDR Detail · Film: Emerald · Film: Velvia · Natural: Vivid Pop | Standard |
| Vintage Lens | Film: Faded Vintage · Film: Instant Photo · B&W: Sepia · Auteur: Hong Kong 90s | Gentle |
| Film Camera 35mm | Film: Portra Golden · Film: Olive Signature · Film: Kodachrome · Film: Travel Ektar · Auteur: Mood for Love | Natural |
| Heavy Film Grain | B&W: Classic Silver · B&W: Hard Noir · Film: Bleach Bypass · Auteur: Nordic Noir | Standard |
| Pro-Mist Cinema | Cinema: Teal & Orange · Auteur: Mood for Love · Auteur: 2046 · Auteur: Golden Anamorphic | Keep the Mood |
| Anamorphic Flare | Cinema: Blockbuster · Cinema: Desert Heat · Auteur: Golden Anamorphic · Cinema: Teal & Orange | Standard |
| Night City Glow | Auteur: Chungking Neon · Mood: Cyberpunk Neon · Film: Red Neon Night · Auteur: Saigon Rain | Keep the Mood |
| Landscape Aerial Haze | Film: Velvia · Mood: Golden Hour · Mood: Autumn Warmth · B&W: Infrared · Cinema: Day for Night | Standard |
| Foggy Morning | Natural: Soft Matte · Mood: Blue Hour · Auteur: Nordic Noir · Mood: Arctic Cold | Keep the Mood |
| Backlit Rim Light | Mood: Golden Hour · Portrait: Golden Skin · Auteur: Golden Anamorphic · Mood: Lavender Dusk | Keep the Mood |
| Dusty Night Film | Cinema: Dusty Night · Cinema: Neo-Noir Blue · Cinema: Moody Dark · Auteur: Fallen Angels | Keep the Mood |
| Digital Flash | Mood: Flash Snapshot · Film: Cross Process · Natural: Vivid Pop | Natural |
| Anamorphic Night | Cinema: Neo-Noir Blue · Auteur: Saigon Rain · Cinema: Digital Green · Auteur: 2046 | Keep the Mood |
| Star Filter Night | Auteur: Happy Together · Mood: Blue Hour · Film: Tungsten Amber | Keep the Mood |
| Cathedral Light | Film: Tungsten Amber · Cinema: Moody Dark · Auteur: Sickly Thriller · B&W: Classic Silver | Keep the Mood |
| Miniature World | Mood: Anime Vivid · Natural: Vivid Pop · Auteur: Pastel Symmetry · Film: Kodachrome | Standard |
| Swirly Vintage Portrait | Auteur: Pastel Symmetry · Film: Emerald · Film: Olive Signature · Mood: Autumn Warmth | Gentle |
| Soap Bubble Bokeh | Film: Velvia · Mood: Golden Hour · Portrait: Soft Glamour | Gentle |
| VHS Home Video | Film: Instant Photo · Film: Faded Vintage · Auteur: Hong Kong 90s | Repair Only |
| CRT Screen | Cinema: Digital Green · Mood: Cyberpunk Neon · B&W: Hard Noir | Repair Only |
| Hexagon Night Bokeh | Mood: Cyberpunk Neon · Auteur: Happy Together · Film: Red Neon Night · Auteur: Chungking Neon | Keep the Mood |
| Glitch Art | Splash: Neon Blue · Mood: Cyberpunk Neon · Cinema: Digital Green | Repair Only |
| Retro Glass | Portrait: Editorial Crisp · Film: Portra Golden · Auteur: Matte Street · Film: Faded Vintage | Natural |
| Retro Glass Deep | Film: Portra Golden · Auteur: Mood for Love · Film: Emerald · Portrait: Golden Skin | Natural |

Keep the Mood is the right correction for any picture whose colour or
darkness is the point (night, neon, candle light, fog); Repair Only for
looks that deliberately degrade the picture; Old Photo Scan for real scans.

## What Auto does

| Step | Detects | Fixes |
|---|---|---|
| JPEG blocking | How much stronger the steps across the 8x8 JPEG grid are than inside the blocks (about 1.0 when clean, 1.3 at quality 50, 1.7+ at quality 20), on the full-size picture | De-blocking along the grid and de-ringing round edges, as strong as the blocking measured (moved here from Digital Mastering) |
| Noise | The noise level (Immerkaer's method) over the flatter half of the picture, so texture is not taken for noise | Colour noise smoothed hard, luminance noise gently and only away from edges |
| Colour cast | The colour of the bright near-neutral pixels (a white shirt, a cup, clouds), on both axes: warm/cool and green/magenta | White balance in linear light, by the size of the cast. Warm and cool light within an everyday range is kept as natural light; green and magenta casts get almost no allowance |
| Black & white points | Clearly milky blacks or dull whites (0.5 % and 99.5 % percentiles) | Levels, part of the way, so pictures keep their own range |
| Exposure | A median brightness outside the normal band, or clipped whites | Exposure in linear light, with a shoulder so black stays black and white stays white; brought to the edge of the band, not to one "correct" grey |
| Contrast | A flat or harsh histogram (its middle half) | A gentle S-curve around the picture's own middle grey |
| Colour strength | Nearly colourless or overcooked colour (muted colour is left alone: it is usually a choice) | A modest vibrance: weak colours move most, skin and strong colours least |
| Reference (optional) | Your reference picture | Its colour and spread (mean and deviation in Lab), at Reference strength |
| Horizon (off by default) | The tilt of the long straight edges near horizontal and vertical (horizons, buildings, door frames), from the structure tensor, with a confidence | Turns the picture level and scales it just enough to hide the corners; only when confident (streets, buildings), never for pictures without straight lines. Done after Overall strength, so the turned and the original picture never mix |

**Guards** keep deliberate pictures as they are:

- **Low-key** (dark with real highlights: night, neon, a lit face): no lift,
  no levels, no contrast or colour boost; a cast is corrected by half.
- **High-key** (bright with real darks: snow, white backdrops): not pulled down.
- **Black & white or toned** (sepia, cyanotype): no colour fixes.
- **No neutrals to measure** (golden hour, neon): the colour is left alone.
- **Almost one tone** (a plain backdrop): the tone is left alone.
- **Keep mood** keeps a share of any cast it finds.

Skin tone is not corrected on its own: without a person detector, orange
clothes, wood and coffee measure as skin. A cast on skin is fixed by the white
balance; Digital Mastering's HSL (orange, red) adjusts skin by hand.

Each step has an on/off box and a strength slider; **Overall strength**
(default 0.8) blends the whole correction with the original.

## Presets

A ticked fix is permission, not an order: Auto measures first and skips a fix
when there is nothing to fix, so a sound picture looks the same under every
preset. The presets differ in which fixes they allow. Pick one from the
carousel; Reset goes back to the stock settings.

| Preset | Allows |
|---|---|
| Standard | Every fix, each only as far as it measures a fault. Horizon off |
| Natural | Faults only: blocking, noise, colour cast, exposure. Contrast and colour left as generated |
| Gentle | Everything at half strength |
| Full Fix | Everything at full strength, horizon levelling included |
| Keep the Mood | For a deliberately warm, cool or dark picture: keeps its cast, contrast and colour |
| Repair Only | JPEG blocking and noise |
| Tone Only | Black & white points, exposure and contrast |
| Old Photo Scan | Every fix at full, no low-key / high-key protection |

A preset never touches the reference picture or its strength. The X/Y/Z plot
has a `[ACC] Preset` axis too.

## What it found

The console prints a line per image, and PNG info carries it:

    Auto Color Corrector found: cast: warm 0.10, green 0.24 -> corrected · levels: 0.00..0.96 -> 0..1

## X/Y/Z plot

Axes for the X/Y/Z plot script, under `[ACC]`: Preset, Overall strength, Keep mood,
and on/off for each fix (colour cast, black & white points, exposure,
contrast, colour strength, JPEG blocking, noise, horizon, low-key / high-key
guard). A cell that sets any of
them switches the corrector on for that cell.

## PNG info

`Auto Color Corrector` holds the settings that differ from the defaults
(`on` for a stock run); Send to / Paste restores them. The reference picture
is not stored.

## Files

```
scripts/auto_color_corrector.py   UI + host hook
lib_acc/auto.py                   measuring, guards and the plan of corrections
lib_acc/ops.py                    the colour maths, pure torch
lib_acc/repair.py                 JPEG blocking, noise and horizon: measuring and fixing
lib_acc/controls.py               every control, declared once (UI, PNG info)
lib_acc/xyz.py                    X/Y/Z plot axes
lib_acc/presets.py                the eight presets
lib_acc/carousel.py               the preset carousel (HTML)
javascript/acc_carousel.js        the preset carousel (clicks, filter, scroll)
preset_icons/                     the preset icons, one picture per preset
lib_acc/reference.py              the folded before / after picture
reference.jpg                     the before / after picture
style.css                         reference box, preset carousel
```

## Credits

- Started as a conversion of
  [ComfyUI-EasyColorCorrector](https://github.com/regiellis/ComfyUI-EasyColorCorrector)
  by Regi E. (MIT); the Auto correction has since been rewritten.
- Sample photos in `reference.jpg`, from scikit-image's sample data:
  Eileen Collins by NASA (public domain), coffee cup by Rachel Michetti (CC0),
  Falcon 9 launch by SpaceX (public domain).
- Preset icons (`preset_icons/`): photos from the Open Images dataset, by Flickr
  photographers under CC BY 2.0 (each author and source listed in
  `preset_icons/CREDITS.md`), cropped, with the preset applied and lettering in
  Bebas Neue (SIL Open Font License 1.1; only the rendered pictures are shipped).

Thanks also to **Claude**, for help building this
extension.

## License

MIT, see `LICENSE` and `NOTICE.md`.
