# NuclearOps UI redesign (Apple-style) — change log

This is a visual and interaction redesign of the NuclearOps Flask app (SOFE 3700U, Phase III).
**No backend behaviour changed.** No Python file (`app.py`, `api.py`, `auth.py`, `db.py`,
`validation.py`, `weather.py`, `export.py`, `config.py`, `init_db.py`), SQL file, route, API
endpoint, database query, or validation rule was edited. Every element ID and form field `name`
that the page scripts use is still the same, so all the existing JavaScript logic (search,
filters, auto-fill, validation, CRUD through `apiRequest`) still works.

Files changed:

| File | Kind of change |
|---|---|
| `static/css/style.css` | Rewritten completely |
| `static/js/common.js` | Message functions replaced; spring, sheet, toast and chart-theme helpers added |
| `templates/base.html` | Header markup, theme-color meta tags, message area moved |
| `templates/login.html` | App icon added, button text changed |
| `static/js/work_orders.js`, `equipment.js`, `workers.js` | Form show/hide lines now call `openSheet` / `closeSheet` |
| `static/js/dashboard.js`, `weather.js` | Chart colours come from CSS variables; `applyChartTheme()` called |
| `.claude/launch.json` | New. Only used to preview the app in the Claude desktop app |

The other templates (`dashboard.html`, `equipment.html`, `workers.html`, `work_orders.html`,
`weather.html`, `reports.html`, `report_view.html`, `error.html`) were **not edited**. They pick
up the new look only through the CSS and `base.html`.

---

## 1. `static/css/style.css` (full rewrite)

The class names are the same as before (`.card`, `.stat`, `.grid-2`, `.grid-4`, `.toolbar`, `.field`,
`.form-grid`, `.wide`, `.tag`, `.message`, `.hint`, `.autofill`, `.view-card`, `.chart-box`,
`.hidden`, `.invalid`, `button.secondary/.danger/.small`, `.login-page`, `.login-box`,
`.demo-logins`, etc.), so the templates and the HTML that JS builds did not need changing. A few
new classes were added (listed below).

### Colour tokens and dark mode
- Old palette (navy `#14263d`, `#2b6cb0` blue, Segoe UI) replaced by Apple system colours as
  CSS variables on `:root`: `--blue #007aff`, `--red #ff3b30`, `--orange #ff9500`,
  `--green #34c759`, `--gray #8e8e93`.
- Surface tokens: `--bg #f2f2f7` (page), `--card #fff`, `--fill` (translucent gray for inputs
  and secondary buttons), `--fill-strong`, `--separator` (hairline lines), `--material` (see-through
  bar background), `--scrim` (dimmed background behind sheets), plus `--text`, `--muted`,
  `--faint`, and tinted versions `--blue-tint`, `--red-tint`, `--orange-tint`, `--green-tint`.
- `@media (prefers-color-scheme: dark)` sets all of those again with Apple's dark values
  (black page, `#1c1c1e` cards, brighter accent colours). **The app follows the OS light/dark
  setting automatically.** `color-scheme: light dark` makes native controls (date pickers,
  scrollbars) match.
- Radii: `--radius 14px` (cards), `--radius-sm 10px` (inputs/buttons). Shadows `--shadow-sm` and
  `--shadow-lg`.

### Typography
- Font: `-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, "Segoe UI", Roboto` (San
  Francisco on Mac, Segoe UI on Windows).
- Base size 15px (`0.9375rem`), slight negative letter-spacing.
- `h1` is a 34px "Large Title" (weight 700, tight line-height 1.12, tracking −0.026em). Large
  text gets tighter letter-spacing, small text is left near 0, following Apple's type guidance.
- Numbers in tables and stat tiles use `font-variant-numeric: tabular-nums` so the digits line up.

### Top navigation (`.navbar`)
- `position: sticky` and see-through with `backdrop-filter: blur(20px) saturate(180%)`, so the
  page scrolls underneath. A hairline shadow replaces the solid navy bar.
- The nav links sit inside a new `.segmented` wrapper styled like an iOS segmented control. The
  active page (existing `.active` class) is a raised white pill.
- New classes: `.brand-mark` (yellow/orange rounded square with ☢), `.brand-name` (the "Ops"
  part is muted), `.avatar` (circle with the user's first initial), `.user-name`. `.role-badge` is
  now a small gray uppercase chip.
- Under 980px wide the nav wraps onto its own row and scrolls sideways; the username text is
  hidden (avatar and role stay).

### Layout and cards
- `main`: max width 1240px, more top padding, safe-area padding for phones.
- `.card`: no border, 14px radius, soft shadow (none in dark mode).
- `.grid-4` becomes 2 columns (it used to be 1) under 900px.

### Stat tiles (`.stat`)
- The coloured left border is gone. The label sits **above** the number (via
  `flex-direction: column-reverse`, so the HTML order didn't change) and starts with a small
  coloured dot: blue by default, orange for `.warn`, red for `.danger`. In `.danger` the number
  itself is also red.

### Tables
- Header row: no fill, small gray labels.
- Hairline row separators, no line under the last row, first/last cells line up with the card
  edge, hover highlights the whole row with `--fill`.
- The last column (Edit/Delete buttons) is right-aligned.
- `.empty` messages are centred with extra padding. `td.null` is faint italic.

### Tags (`.tag`)
- Fully rounded pills on tinted backgrounds. Critical = red, High and In-Progress = orange,
  Medium and Open = blue, Completed = green, Low and Cancelled = gray (the default).

### Form controls
- `input`, `select` and `textarea` have no border, a filled gray background, 10px radius and 36px
  minimum height. On focus the background turns to the card colour with a blue ring.
- `select` uses `appearance: none` with an inline SVG up/down chevron.
- `.invalid` (still added by `markInvalid()`) shows a red tint and a red ring.
- `.autofill` (the location box on the work order form) is a light blue tinted box.
- `.form-grid` is 3 columns and drops to 1 column under 760px. Inline `grid-column: span 2` styles
  are overridden there.

### Buttons
- Primary: solid blue, white text, 600 weight, 10px radius.
- `.secondary`: gray fill with blue text. `.danger`: red tint with red text. `.small`: 28px tall
  and fully rounded (used for the Edit/Delete buttons in table rows).
- **Press feedback on pointer-down:** `:active` shrinks the button to `scale(0.97)` and darkens it
  slightly, with a 60ms transition so it responds immediately. `touch-action: manipulation` removes
  the mobile tap delay.
- Visible focus ring for keyboard users. `:disabled` is shown at 40% opacity.

### Messages and toasts (`#message-area`, `.message`)
- `#message-area` is now `position: fixed` at the top centre with `z-index: 200`, above the navbar
  and above open sheets.
- `.message` is a floating see-through card with blur and a coloured left accent (green =
  success, red = error, blue = info). New `.message .close` style for the round ✕ button.

### Sheets (new: `.scrim`, `.card.sheet`, `.sheet-grabber`, `body.sheet-open`)
- `.scrim`: full-screen dimming layer behind the sheet. JavaScript sets its opacity.
- `.card.sheet`: the create/edit form card becomes a fixed panel, max 760px wide and centred. On
  phones it is attached to the bottom with rounded top corners; on desktop (≥761px) it floats 24px
  above the bottom with all corners rounded. It scrolls inside itself if the form is tall, and it
  starts off-screen (`translate(-50%, 100%)`).
- `.sheet-grabber`: the small handle bar at the top. It stays visible while the sheet scrolls and
  is the drag target.
- The Save/Cancel row inside a sheet is right-aligned with Save on the right
  (`flex-direction: row-reverse`), as on macOS.
- `body.sheet-open` stops the page behind the sheet from scrolling.

### Login page
- Light gray background with two soft coloured radial glows (yellow top-left, blue bottom-right).
- `.login-box`: centred card with 22px radius and a large shadow, a 56px app icon, and 44px tall
  inputs and button.
- Login errors show as a red-tinted box. This box isn't in `#message-area`, so its `.message`
  styles are reset there.
- The demo accounts table uses a monospace font.

### Reports list (`.view-card`)
- Rounded cards with a chevron (›) on the right, the "View N" label in small blue text above the
  title, a lift on hover and a slight shrink on press.

### Accessibility media queries
- `prefers-reduced-motion: reduce`: all CSS transitions are set to 0 and the press-shrink is
  turned off. The JS springs also jump straight to their end value (see below).
- `prefers-reduced-transparency: reduce`: the navbar and toasts get solid backgrounds with no blur.
- `prefers-contrast: more`: cards and the navbar get solid outlines, and inputs get visible borders.

---

## 2. `static/js/common.js`

**Unchanged:** `apiRequest`, `escapeHtml`, `show`, `tag`, `today`, `fillSelect`,
`formToObject`, `fillForm`, `markInvalid`, the input/change listeners that remove `.invalid`,
`canEdit`, `isAdmin`.

**Replaced:** `showMessage`, `showError` and `clearMessage` keep the **same names and
arguments**, so every existing call still works, but they now show toasts (section 2.4).

**Added** (between the message helpers and `escapeHtml`):

### 2.1 Springs: `createSpring(initial, onUpdate)`
- A small spring animation, written by hand so no library is needed (no bundler, no CDN). It is set
  the way Apple sets springs: **damping ratio** (1 = no bounce, <1 = overshoot) and
  **response** (seconds).
- Physics: mass 1, stiffness `k = (2π / response)²`, damping `c = 4π · damping / response`. It
  steps forward in time with semi-implicit Euler in small slices (≤ 1/240s) on every
  `requestAnimationFrame`. The time step is capped at 64ms so a slow frame doesn't make it jump.
- `spring.to(target, { damping, response, velocity, done })` starts from the **current** value
  and velocity. That means an animation can be interrupted or redirected mid-way without jumping.
- `spring.set(value)` jumps to a value (used while dragging). `spring.stop()` cancels the animation.
- It counts as settled when the speed is under 2px/s and it is within 0.5px of the target; it then
  calls `done`.
- If the user prefers reduced motion (`REDUCED_MOTION` matchMedia), `to()` jumps straight to the
  target with no animation.

### 2.2 Gesture helpers
- `projectMomentum(velocity, rate = 0.998)`: Apple's formula for where a flick would come to rest:
  `(v/1000) · rate / (1 − rate)`.
- `rubberband(overshoot, dimension)`: resistance that grows the further you drag past an edge
  (constant 0.55).

### 2.3 Sheets: `openSheet(card)` / `closeSheet(card, velocity)`
- `setupSheet(card)` runs once per form card. It:
  - adds the `.sheet` class and `role="dialog"` / `aria-modal`;
  - adds a `.sheet-grabber` div at the top of the card;
  - creates a spring that sets `transform: translate(-50%, Ypx)` and fades the scrim with
    `opacity = 1 − Y / closedOffset` (closedOffset = sheet height + 40px).
- **Drag to dismiss:** dragging the grabber or the sheet's `<h2>` uses Pointer Events with
  `setPointerCapture`. The sheet follows the pointer 1:1 from where it was grabbed. Dragging
  upward past the top is rubber-banded. It records the last 6 pointer positions to work out the
  release speed. On release it projects where the sheet would end up (`rate 0.99`):
  - past 40% of the sheet height → close, keeping the drag's speed;
  - otherwise → spring back to the open position (`damping 0.8, response 0.3`, starting at the
    drag's speed, so there is a little bounce because it was thrown).
- `openSheet(card)`: removes `.hidden`, adds `body.sheet-open`, shows the scrim, starts the sheet
  off-screen if it was hidden, and springs it to Y = 0 (`damping 1, response 0.38`, no bounce).
  It then focuses the first input with `preventScroll`.
- `closeSheet(card, velocity)`: springs the sheet back down off-screen (`damping 1, response 0.32`,
  keeping any flick speed), takes the dimming away as it goes, and adds `.hidden` when it
  finishes, unless the sheet was reopened meanwhile.
- A shared scrim element is created lazily. Clicking it closes the sheet.
- A global **Escape** key handler closes the open sheet.

### 2.4 Toasts
- `showMessage(text, type, details)` dismisses any current toasts, builds a new
  `.message <type>` div (the text and optional `<ul>` of details, all escaped with `escapeHtml`)
  and adds it to `#message-area`.
- `presentToast(toast, type)` adds the ✕ close button and springs the toast in from −24px with a
  fade. **Success and info toasts disappear after 4.5s; error toasts stay until closed.**
- `dismissToast(toast)` springs the toast up and out, then removes it.
- `clearMessage()` dismisses all toasts (with animation now, instead of wiping `innerHTML`).
- The old `window.scrollTo({top: 0})` in `showMessage` was removed. It isn't needed because toasts
  are fixed on screen.
- When the page loads, flashed Flask messages already in `#message-area` are turned into
  info toasts.

### 2.5 Chart styling
- `cssColor(name)` reads a CSS variable from `:root`, so charts use the correct colour for light
  or dark mode.
- `applyChartTheme()` sets Chart.js defaults:
  - system font, 12px, muted text colour, hairline grid lines with no axis border or tick marks;
  - circular legend markers, rounded tooltips;
  - bars with 6px rounded corners (`borderSkipped: false`);
  - smooth lines (`tension 0.35`, width 2.5) with points shown only on hover;
  - 600ms animation, or 0 with reduced motion.

  If Chart.js isn't loaded, it does nothing.

---

## 3. `templates/base.html`
- Added two `<meta name="theme-color">` tags (`#f2f2f7` light, `#000` dark) so the mobile browser
  bar matches the page.
- Brand: `<div class="brand"><span class="brand-mark">☢</span><span class="brand-name">Nuclear<span>Ops</span></span></div>`.
- `<nav aria-label="Main">` now wraps the links in `<div class="segmented">`. The links, URLs and
  the `active` logic are the same.
- User area: `.avatar` (first letter of `current_user`), `.user-name`, `.role-badge`, Log out
  link.
- **Flashed messages moved inside `#message-area`** (which now has `role="status"
  aria-live="polite"`), so they appear as toasts instead of banners above the page content.
- The `CURRENT_ROLE` script and the script includes are unchanged.

## 4. `templates/login.html`
- Added `<div class="brand-mark">☢</div>` above the "NuclearOps" heading.
- The submit button text changed from "Log in" to "Sign In". The form, field names,
  `novalidate`, the inline validation script and the demo accounts table are unchanged.

## 5. `static/js/work_orders.js`, `equipment.js`, `workers.js`
The only edits are the show/hide calls for the form card:
- In `openForm()`: `formCard.classList.remove("hidden"); formCard.scrollIntoView(...)` became
  `openSheet(formCard);`
- In the Cancel button handler and after a successful save:
  `formCard.classList.add("hidden")` became `closeSheet(formCard)`.

Everything else (loading, filtering, auto-fill, validation, the create/update/delete calls) is
untouched. The form cards in the templates still start with `class="card hidden"`. The `.sheet`
class is added by JS the first time a form is opened.

## 6. `static/js/dashboard.js` and `weather.js`
- `applyChartTheme();` is called once at the top (Chart.js is loaded before these scripts).
- Hard-coded hex colours were replaced with `cssColor(...)`:
  - Dashboard `PRIORITY_COLOURS`: Critical `--red`, High `--orange`, Medium `--blue`, Low `--gray`.
  - Dashboard `STATUS_COLOURS`: Open `--blue`, In Progress `--orange`, Completed `--green`,
    Cancelled `--gray`.
  - Outage chart: Planned days `--fill-strong` (gray), Actual days `--blue`.
  - Weather chart: Temperature `--red`, Wind `--blue`.
- The chart types, data, axes and API calls are unchanged.

---

## 7. Testing and preview setup (not part of the app)
- The Mac has only Python 3.8 (the README needs 3.10+), so the app was run from a temporary
  Python 3.12 virtual environment outside the project, with a small wrapper script that changes
  `config.DB_NAME` to `nuclearops_preview` and `DB_USER` to the local Postgres user **in memory
  only**. `config.py` itself was not changed.
- A separate local database, `nuclearops_preview`, was created and filled with `init_db.py`. It
  was kept on purpose. Remove it with `dropdb -h localhost nuclearops_preview`.
- `.claude/launch.json` was added so the Claude desktop app can start that preview on port 5055.
  It points to the temporary environment and is not needed to run the project normally
  (`python app.py` still works as described in the README).
- Checked:
  - signing in as admin;
  - the Dashboard, Work Orders, Equipment, Workers, Outage Weather and Reports pages (all returned
    200 and rendered);
  - opening the New work order sheet, submitting it empty (the error toast appeared above the
    sheet), and closing it with Escape;
  - light mode, dark mode, and 375px phone width (no sideways scrolling).
- **Not checked:** dragging a sheet with a real mouse or finger, Safari, and the Edit/Delete flows
  after the change.

## 8. How this maps to the Phase III requirements
Nothing was removed. The items in README section 5 (sessions, roles, validation, REST API,
external API, CRUD, export, error handling, AJAX/Fetch, Chart.js charts, search and filter,
dynamic forms with auto-fill) all work as before. Browser-side validation still uses
`markInvalid()` and `showMessage(..., "error", errors)`; the errors now appear in a toast that
stays visible above the form sheet.
