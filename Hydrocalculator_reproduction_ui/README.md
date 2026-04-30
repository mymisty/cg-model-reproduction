# HydroCalculator reproduction UI

This folder contains a static, offline reproduction of the HydroCalculator 1.04 calculation workflow.

- `hydrocalc-core.js` contains the formulas restored from `HydroCalculator_104.exe` IL.
- `app.js` contains browser UI behavior.
- `index.html` can be opened directly in a browser.

The batch CSV input follows the original `inputdata_104.csv` header order. Results are rounded to 4 decimal places with away-from-zero midpoint rounding to match the original .NET behavior.

Option mapping:

- `opc=1`: ambient air moisture `d2HA` and `d18OA` are entered directly.
- `opc=2`: ambient air moisture is calculated from rain isotope values.
- `opc=3`: the app searches the original `x` adjustment range, `0.6001` to `1.0000`, and uses the first value after the LEL fit stops improving, matching the original executable's behavior.
