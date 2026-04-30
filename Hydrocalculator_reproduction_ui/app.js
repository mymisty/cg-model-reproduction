const core = window.HydroCalcCore;

const state = {
  rows: [],
  columnMode: "primary",
};

const manualForm = document.querySelector("#manualForm");
const manualStatus = document.querySelector("#manualStatus");
const batchStatus = document.querySelector("#batchStatus");
const resultCount = document.querySelector("#resultCount");
const metricStrip = document.querySelector("#metricStrip");
const resultsTable = document.querySelector("#resultsTable");
const csvText = document.querySelector("#csvText");
const downloadButton = document.querySelector("#downloadButton");

function selectedValue(name) {
  return document.querySelector(`input[name="${name}"]:checked`)?.value;
}

function setOptionVisibility() {
  const option = selectedValue("option");
  document.querySelectorAll("[data-option-field]").forEach((field) => {
    const allowed = field.dataset.optionField.split(" ");
    field.classList.toggle("is-hidden", !allowed.includes(option));
  });
}

function formToRecord() {
  const data = new FormData(manualForm);
  const record = {};
  core.INPUT_HEADERS.forEach((header) => {
    record[header] = data.get(header) || "";
  });
  record.opc = selectedValue("option");
  return record;
}

function setManualOption(option) {
  const radio = document.querySelector(`input[name="option"][value="${option}"]`);
  if (radio) {
    radio.checked = true;
  }
  setOptionVisibility();
}

function fillManual(record) {
  setManualOption(record.opc || "1");
  core.INPUT_HEADERS.forEach((header) => {
    const input = manualForm.elements[header];
    if (input && record[header] !== undefined) {
      input.value = record[header];
    }
  });
}

function calculateManual() {
  const row = core.computeRow(formToRecord());
  state.rows = [row];
  manualStatus.textContent = row.errors?.length ? row.errors.join("; ") : "完成";
  render();
}

function calculateBatchFromText() {
  const records = core.parseCSV(csvText.value);
  if (records.length === 0) {
    state.rows = [];
    batchStatus.textContent = "没有可计算的记录";
    render();
    return;
  }
  state.rows = core.calculateBatch(records);
  const errors = state.rows.filter((row) => row.errors?.length).length;
  batchStatus.textContent = errors ? `${records.length} 条，${errors} 条有错误` : `${records.length} 条完成`;
  render();
}

function renderMetrics(row) {
  metricStrip.innerHTML = "";
  if (!row || row.errors?.length) {
    return;
  }

  const model = selectedValue("model");
  const metrics =
    model === "steady"
      ? [
          ["E/I δ²H", row.EI_H],
          ["E/I δ¹⁸O", row.EI_O],
          ["δ²HA", row.d2HA],
          ["δ¹⁸OA", row.d18OA],
        ]
      : [
          ["f δ²H", row.f_H],
          ["f δ¹⁸O", row.f_O],
          ["δ²HA", row.d2HA],
          ["δ¹⁸OA", row.d18OA],
        ];

  metrics.forEach(([label, value]) => {
    const metric = document.createElement("div");
    metric.className = "metric";
    metric.innerHTML = `<span>${label}</span><strong>${core.formatValue(value)}</strong>`;
    metricStrip.append(metric);
  });
}

function renderTable() {
  resultsTable.innerHTML = "";
  const headers = state.columnMode === "all" ? core.OUTPUT_HEADERS : core.PRIMARY_HEADERS;

  if (state.rows.length === 0) {
    const tbody = document.createElement("tbody");
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.className = "empty-state";
    cell.colSpan = 1;
    cell.textContent = "暂无结果";
    row.append(cell);
    tbody.append(row);
    resultsTable.append(tbody);
    return;
  }

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headers.forEach((header) => {
    const th = document.createElement("th");
    th.textContent = header.trim() || " ";
    headRow.append(th);
  });
  thead.append(headRow);
  resultsTable.append(thead);

  const tbody = document.createElement("tbody");
  state.rows.forEach((result) => {
    const row = document.createElement("tr");
    if (result.errors?.length) {
      row.className = "error-row";
    }
    headers.forEach((header, index) => {
      const td = document.createElement("td");
      td.textContent =
        result.errors?.length && index === 0
          ? `${result[header] || "Error"}: ${result.errors.join("; ")}`
          : core.formatValue(result[header]);
      row.append(td);
    });
    tbody.append(row);
  });
  resultsTable.append(tbody);
}

function render() {
  resultCount.textContent = `${state.rows.length} 条记录`;
  downloadButton.disabled = state.rows.length === 0;
  renderMetrics(state.rows[0]);
  renderTable();
}

function downloadCSV() {
  if (state.rows.length === 0) {
    return;
  }
  const blob = new Blob([core.toCSV(state.rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "hydrocalculator-results.csv";
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function loadSample() {
  csvText.value = core.SAMPLE_CSV;
  const first = core.parseCSV(core.SAMPLE_CSV)[0];
  fillManual(first);
  calculateBatchFromText();
}

document.querySelector("#calculateManualButton").addEventListener("click", calculateManual);
document.querySelector("#calculateBatchButton").addEventListener("click", calculateBatchFromText);
document.querySelector("#loadSampleButton").addEventListener("click", loadSample);
document.querySelector("#downloadButton").addEventListener("click", downloadCSV);
document.querySelector("#clearButton").addEventListener("click", () => {
  state.rows = [];
  csvText.value = "";
  batchStatus.textContent = "未载入";
  manualStatus.textContent = "待输入";
  render();
});

document.querySelector("#csvFileInput").addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }
  const reader = new FileReader();
  reader.addEventListener("load", () => {
    csvText.value = String(reader.result || "");
    batchStatus.textContent = file.name;
    calculateBatchFromText();
  });
  reader.readAsText(file);
});

document.querySelectorAll('input[name="option"]').forEach((input) => {
  input.addEventListener("change", setOptionVisibility);
});

document.querySelectorAll('input[name="model"]').forEach((input) => {
  input.addEventListener("change", () => renderMetrics(state.rows[0]));
});

document.querySelectorAll('input[name="columnMode"]').forEach((input) => {
  input.addEventListener("change", () => {
    state.columnMode = selectedValue("columnMode");
    renderTable();
  });
});

setOptionVisibility();
csvText.value = core.SAMPLE_CSV;
render();
