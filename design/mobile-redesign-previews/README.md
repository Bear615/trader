# Mobile Redesign Preview Batch

This folder contains a deterministic preview batch for the Trader mobile redesign. The images are app-screen previews, not marketing slides.

## Output Specs

- Canvas: 390 x 844 px, iPhone-style portrait preview.
- Density: exported at 1x PNG for quick review and issue comments.
- Layout: single-column mobile content with fixed bottom navigation.
- Safe spacing: 14 to 16 px screen gutters, 8 to 12 px component gaps.
- Corner radius: 8 px for panels, controls, and rows.
- Typography: system sans stack, no viewport-scaled type.
- Numbers: tabular numeric styling for prices, balances, P&L, confidence, and percentages.
- Palette: graphite base with emerald, rose, amber, and cyan accents. No one-color blue/slate wash.
- Navigation: six primary destinations retained from the app: Home, Trades, AI, Monitor, Test, Admin.
- Data model: XRP/USD examples, portfolio value, cash, XRP balance, trades, AI decisions, backtest runs, risk settings.

## Screens

1. `01-dashboard.png` - account value, live XRP price, chart, key portfolio metrics.
2. `02-portfolio.png` - exposure, cash, XRP allocation, entry, risk capacity.
3. `03-trades.png` - trade history rewritten as mobile cards instead of a compressed table.
4. `04-trade-detail.png` - audit view for one execution.
5. `05-ai-decisions.png` - decision log, filters, trigger action, distribution.
6. `06-ai-detail.png` - decision response, amount, confidence, model, raw JSON collapsed.
7. `07-monitor.png` - mobile replacement for the desktop split-pane AI monitor.
8. `08-backtest-setup.png` - stepwise backtest configuration.
9. `09-backtest-results.png` - backtest result metrics, equity chart, run history.
10. `10-admin.png` - grouped admin settings, live trading guard, risk controls.

## Needed

- Mobile-first summaries for finance data, not desktop tables squeezed into narrow width.
- Immediate visibility for portfolio value, current price, exposure, cash, risk, and active mode.
- AI decisions that show action, confidence, execution state, model, and failure/retry state.
- Detail screens for audit-heavy records instead of showing every column in list views.
- Bottom navigation because all six current destinations matter in the existing app.
- Guarded live mode controls and risk settings in Admin.
- Export, raw prompt, raw response, and danger actions still available, but secondary.

## Not Needed

- Landing, hero, onboarding, or feature-tour screens.
- Decorative 3D assets, fake mascots, large illustrations, or abstract gradient backgrounds.
- A desktop sidebar on mobile.
- Full-width tables with nine columns.
- Raw JSON or raw prompt text as the first thing a normal user sees.
- Prominent reset, seed, clear, or destructive admin actions.
- Extra crypto pairs beyond the current XRP/quote-currency app model.

## Render

Run `render-mobile-previews.ps1` from this folder or the repo root. It uses the installed Chrome or Edge executable in headless mode.
