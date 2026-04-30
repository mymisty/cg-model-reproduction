(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.HydroCalcCore = api;
})(typeof globalThis !== "undefined" ? globalThis : window, function () {
  const INPUT_HEADERS = [
    "hydrocal=Sample name",
    "opc",
    "T",
    "h",
    "d2HP",
    "d18OP",
    "d2HL",
    "d18OL",
    "d2HA",
    "d18OA",
    "d2HR",
    "d18OR",
    "CkH",
    "CkO",
    "LEL",
    "comment",
  ];

  const OUTPUT_HEADERS = [
    ...INPUT_HEADERS,
    "     ",
    "EkH",
    "EkO",
    "EplusH",
    "EplusO",
    "EH",
    "EO",
    "aplusH",
    "aplusO",
    "dstarH",
    "dstarO",
    "mH",
    "mO",
    "x",
    "    ",
    "EI_H",
    "EI_O",
    "f_H",
    "f_O",
  ];

  const SAMPLE_CSV = [
    "hydrocal=Sample name,opc,T,h,d2HP,d18OP,d2HL,d18OL,d2HA,d18OA,d2HR,d18OR,CkH,CkO,LEL, comment",
    "Sample 1,1,25,0.5,-51.6,-8.05,-40.9,-6.41,-99.9,-13.05,,,12.5,14.2,,test for known dA",
    "Sample 2,2,25,0.5,-51.6,-8.05,-40.9,-6.41,,,-21,-5.1,12.5,14.2,,test for known dR",
    "Sample 3,3,25,0.5,-51.6,-8.05,-40.9,-6.41,,,-21,-5.1,12.5,14.2,4.59,test for known dR and LEL",
  ].join("\n");

  const PRIMARY_HEADERS = [
    "hydrocal=Sample name",
    "opc",
    "d2HA",
    "d18OA",
    "x",
    "EI_H",
    "EI_O",
    "f_H",
    "f_O",
  ];

  function toNumber(value, fallback = 0) {
    if (value === null || value === undefined || value === "") {
      return fallback;
    }
    const n = Number(String(value).trim());
    return Number.isFinite(n) ? n : fallback;
  }

  function roundAway(value, digits = 4) {
    if (!Number.isFinite(value)) {
      return value;
    }
    const factor = 10 ** digits;
    const rounded = Math.round(Math.abs(value) * factor + Number.EPSILON) / factor;
    return Math.sign(value || 1) * rounded;
  }

  function formatValue(value) {
    if (value === null || value === undefined) {
      return "";
    }
    if (typeof value === "number") {
      if (Number.isNaN(value)) {
        return "NaN";
      }
      if (!Number.isFinite(value)) {
        return String(value);
      }
      return String(roundAway(value, 4));
    }
    return String(value);
  }

  function parseCSV(text) {
    const rows = [];
    let field = "";
    let row = [];
    let quoted = false;

    for (let i = 0; i < text.length; i += 1) {
      const char = text[i];
      const next = text[i + 1];

      if (char === '"') {
        if (quoted && next === '"') {
          field += '"';
          i += 1;
        } else {
          quoted = !quoted;
        }
      } else if (char === "," && !quoted) {
        row.push(field);
        field = "";
      } else if ((char === "\n" || char === "\r") && !quoted) {
        if (char === "\r" && next === "\n") {
          i += 1;
        }
        row.push(field);
        if (row.some((cell) => cell.trim() !== "")) {
          rows.push(row);
        }
        row = [];
        field = "";
      } else {
        field += char;
      }
    }

    row.push(field);
    if (row.some((cell) => cell.trim() !== "")) {
      rows.push(row);
    }

    if (rows.length === 0) {
      return [];
    }

    const header = rows[0].map((cell) => cell.trim());
    return rows.slice(1).map((cells) => {
      const record = {};
      INPUT_HEADERS.forEach((name, index) => {
        const headerIndex = header.findIndex((candidate) => candidate.trim() === name);
        const sourceIndex = headerIndex >= 0 ? headerIndex : index;
        record[name] = cells[sourceIndex] === undefined ? "" : cells[sourceIndex].trim();
      });
      return record;
    });
  }

  function escapeCSV(value) {
    const text = formatValue(value);
    return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function toCSV(rows, headers = OUTPUT_HEADERS) {
    const lines = [headers.map(escapeCSV).join(",")];
    rows.forEach((row) => {
      lines.push(headers.map((header) => escapeCSV(row[header])).join(","));
    });
    return lines.join("\n");
  }

  function aplusH(T) {
    const tk = T + 273.15;
    const exponent =
      (1158.8 * tk ** 3) / 1e9 -
      (1620.1 * tk ** 2) / 1e6 +
      (794.84 * tk) / 1000 -
      161.04 +
      (2.9992 * 10 ** 9) / tk ** 3;
    return Math.exp(exponent / 1000);
  }

  function aplusO(T) {
    const tk = T + 273.15;
    const exponent =
      -7.685 +
      (6.7123 * 1000) / tk -
      (1.6664 * 1e6) / tk ** 2 +
      (0.35041 * 10 ** 9) / tk ** 3;
    return Math.exp(exponent / 1000);
  }

  function Eplus(alpha) {
    return (alpha - 1) * 1000;
  }

  function Ek(h, Ck) {
    return (1 - h) * Ck;
  }

  function E(EkValue, EplusValue, alpha) {
    return EkValue + EplusValue / alpha;
  }

  function dstar(h, dA, EValue) {
    return (h * dA + EValue) / (h - EValue / 1000);
  }

  function m(h, EValue, EkValue) {
    return (h - EValue / 1000) / (1 - h + EkValue / 1000);
  }

  function EI(dL, dP, dStar, mValue) {
    return (dL - dP) / ((dStar - dL) * mValue);
  }

  function f(dL, dStar, dP, mValue) {
    return 1 - ((dL - dStar) / (dP - dStar)) ** (1 / mValue);
  }

  function dAFromRain(alpha, dRain, EplusValue) {
    return (dRain - EplusValue) / alpha;
  }

  function dAFromRainAndX(x, dRain, EplusValue) {
    return (dRain - EplusValue * x) / (1 + (x * EplusValue) / 1000);
  }

  function slopeFromX(x, values) {
    const hMoist = dAFromRainAndX(x, values.d2HR, values.EplusH);
    const oMoist = dAFromRainAndX(x, values.d18OR, values.EplusO);

    const hTerm =
      (values.h * (hMoist / 1000 - values.d2HR / 1000) +
        (1 + values.d2HR / 1000) * (values.EH / 1000)) /
      (values.h - values.EH / 1000);
    const oTerm =
      (values.h * (oMoist / 1000 - values.d18OR / 1000) +
        (1 + values.d18OR / 1000) * (values.EO / 1000)) /
      (values.h - values.EO / 1000);

    return hTerm / oTerm;
  }

  function findXForLEL(values, targetLEL) {
    let bestDiff = 1000;
    let selected = 1;
    const target = roundAway(targetLEL, 4);
    const startX = 0.6001;
    const endX = 1;
    const startSlope = roundAway(slopeFromX(startX, values), 4);
    const endSlope = roundAway(slopeFromX(endX, values), 4);
    const lower = Math.min(startSlope, endSlope);
    const upper = Math.max(startSlope, endSlope);

    if (target < lower || target > upper) {
      return Math.abs(startSlope - target) <= Math.abs(endSlope - target) ? startX : endX;
    }

    for (let i = 6001; i <= 10000; i += 1) {
      const x = roundAway(i / 10000, 4);
      const slope = roundAway(slopeFromX(x, values), 4);
      const diff = slope - target;

      if (diff === 0) {
        selected = x;
        break;
      }

      if (Math.abs(diff) > Math.abs(bestDiff)) {
        selected = x;
        break;
      }

      bestDiff = diff;
      selected = x;
    }

    return selected;
  }

  function validateRecord(record) {
    const errors = [];
    const option = String(record.opc || "").trim();
    const common = ["T", "h", "d2HP", "d18OP", "d2HL", "d18OL", "CkH", "CkO"];
    const byOption = {
      1: ["d2HA", "d18OA"],
      2: ["d2HR", "d18OR"],
      3: ["d2HR", "d18OR", "LEL"],
    };

    if (!["1", "2", "3"].includes(option)) {
      errors.push("opc must be 1, 2, or 3");
    }

    [...common, ...(byOption[option] || [])].forEach((key) => {
      const raw = record[key];
      if (raw === "" || raw === null || raw === undefined || !Number.isFinite(Number(raw))) {
        errors.push(`${key} is not numeric`);
      }
    });

    return errors;
  }

  function computeRow(inputRecord) {
    const row = {};
    INPUT_HEADERS.forEach((header) => {
      row[header] = inputRecord[header] ?? "";
    });
    row["     "] = "";
    row["    "] = "";

    const errors = validateRecord(row);
    if (errors.length > 0) {
      row.errors = errors;
      return row;
    }

    const option = String(row.opc).trim();
    const values = {
      T: toNumber(row.T),
      h: toNumber(row.h),
      d2HP: toNumber(row.d2HP),
      d18OP: toNumber(row.d18OP),
      d2HL: toNumber(row.d2HL),
      d18OL: toNumber(row.d18OL),
      d2HA: toNumber(row.d2HA),
      d18OA: toNumber(row.d18OA),
      d2HR: toNumber(row.d2HR),
      d18OR: toNumber(row.d18OR),
      CkH: toNumber(row.CkH),
      CkO: toNumber(row.CkO),
      LEL: toNumber(row.LEL),
    };

    values.EkH = Ek(values.h, values.CkH);
    values.EkO = Ek(values.h, values.CkO);
    values.aplusH = aplusH(values.T);
    values.aplusO = aplusO(values.T);
    values.EplusH = Eplus(values.aplusH);
    values.EplusO = Eplus(values.aplusO);
    values.EH = E(values.EkH, values.EplusH, values.aplusH);
    values.EO = E(values.EkO, values.EplusO, values.aplusO);

    if (option === "2") {
      values.d2HA = dAFromRain(values.aplusH, values.d2HR, values.EplusH);
      values.d18OA = dAFromRain(values.aplusO, values.d18OR, values.EplusO);
      row.d2HA = values.d2HA;
      row.d18OA = values.d18OA;
    }

    if (option === "3") {
      values.x = findXForLEL(values, values.LEL);
      values.d18OA = dAFromRainAndX(values.x, values.d18OR, values.EplusO);
      values.d2HA = dAFromRainAndX(values.x, values.d2HR, values.EplusH);
      row.x = values.x;
      row.d2HA = values.d2HA;
      row.d18OA = values.d18OA;
    } else {
      row.x = "";
    }

    values.dstarH = dstar(values.h, values.d2HA, values.EH);
    values.dstarO = dstar(values.h, values.d18OA, values.EO);
    values.mH = m(values.h, values.EH, values.EkH);
    values.mO = m(values.h, values.EO, values.EkO);
    values.EI_H = EI(values.d2HL, values.d2HP, values.dstarH, values.mH);
    values.EI_O = EI(values.d18OL, values.d18OP, values.dstarO, values.mO);
    values.f_H = f(values.d2HL, values.dstarH, values.d2HP, values.mH);
    values.f_O = f(values.d18OL, values.dstarO, values.d18OP, values.mO);

    [
      "EkH",
      "EkO",
      "EplusH",
      "EplusO",
      "EH",
      "EO",
      "aplusH",
      "aplusO",
      "dstarH",
      "dstarO",
      "mH",
      "mO",
      "EI_H",
      "EI_O",
      "f_H",
      "f_O",
    ].forEach((key) => {
      row[key] = values[key];
    });

    ["T", "h", "d2HP", "d18OP", "d2HL", "d18OL", "d2HA", "d18OA", "d2HR", "d18OR", "CkH", "CkO", "LEL"].forEach(
      (key) => {
        if (row[key] !== "") {
          row[key] = toNumber(row[key]);
        }
      },
    );

    return OUTPUT_HEADERS.reduce((acc, header) => {
      acc[header] = row[header] ?? "";
      return acc;
    }, { errors: [] });
  }

  function calculateBatch(records) {
    return records.map(computeRow);
  }

  return {
    INPUT_HEADERS,
    OUTPUT_HEADERS,
    PRIMARY_HEADERS,
    SAMPLE_CSV,
    calculateBatch,
    computeRow,
    formatValue,
    parseCSV,
    roundAway,
    toCSV,
  };
});
