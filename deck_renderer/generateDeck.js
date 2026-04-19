const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const SHAPE_TYPES = { rect: "rect", line: "line" };
const CHART_TYPES = { bar: "bar" };

const DEFAULT_THEME = {
  layoutName: "DECKCREATOR_WIDE",
  width: 13.333,
  height: 7.5,
  colors: {
    canvas: "F5F1EA",
    ink: "18232B",
    muted: "66727C",
    accent: "0D5C63",
    accentSoft: "DCEEEF",
    line: "D8D2C8",
    card: "FFFDFC",
    stripe: "F0EBE2",
    danger: "8D3B3B",
  },
  fonts: {
    title: "Aptos Display",
    body: "Aptos",
    mono: "Aptos",
  },
  spacing: {
    pageX: 0.7,
    pageY: 0.45,
    pageW: 11.95,
    gutter: 0.24,
    sectionGap: 0.22,
    footerY: 7.0,
  },
  text: {
    heroTitle: 24,
    slideTitle: 20,
    eyebrow: 10,
    body: 12,
    small: 9,
    metric: 21,
    table: 10,
  },
};
let THEME = createTheme();

function main() {
  const payloadPath = process.argv[2];
  if (!payloadPath) {
    throw new Error("Expected a payload JSON path.");
  }

  const payload = JSON.parse(fs.readFileSync(payloadPath, "utf-8"));
  const analysis = payload.analysis;
  const outputPath = payload.outputPath;
  const referencePath = payload.referencePath || "";
  THEME = createTheme(payload.theme || analysis.theme || {});

  ensureDirectory(path.dirname(outputPath));

  const pptx = new PptxGenJS();
  pptx.defineLayout({ name: THEME.layoutName, width: THEME.width, height: THEME.height });
  pptx.layout = THEME.layoutName;
  pptx.author = "DeckCreator";
  pptx.company = "DeckCreator";
  pptx.subject = analysis.title;
  pptx.title = analysis.title;
  pptx.lang = "en-US";
  pptx.theme = {
    headFontFace: THEME.fonts.title,
    bodyFontFace: THEME.fonts.body,
    lang: "en-US",
  };

  addTitleSlide(pptx, analysis, referencePath);
  addKpiSlide(pptx, analysis);
  addTableSlide(pptx, "Channel Performance", analysis.channel_rows || [], "Revenue", "ROI");
  addTableSlide(pptx, "Regional Performance", analysis.region_rows || [], "Revenue", "ROI");
  addTableSlide(pptx, "Top Campaigns", analysis.top_campaign_rows || [], "Revenue", "ROI");
  addInsightSlide(pptx, "Executive Summary", [analysis.executive_summary], {
    subtitle: buildReferenceSubtitle(referencePath),
    sectionLabel: "Overview",
    treatAsSummary: true,
  });
  addInsightSlide(pptx, "Key Insights", analysis.key_insights || [], { sectionLabel: "Insights" });
  addInsightSlide(pptx, "Trends", analysis.trends || [], { sectionLabel: "Signals" });
  addInsightSlide(pptx, "Risks", analysis.risks || [], { sectionLabel: "Risks", accentColor: THEME.colors.danger });
  addTableSlide(pptx, "Workbook Sample", buildSampleRows(analysis.sample_rows || []), ...buildSampleHeaders(analysis.sample_rows || []));

  return pptx.writeFile({ fileName: outputPath });
}

function addTitleSlide(pptx, analysis, referencePath) {
  const slide = createBaseSlide(pptx, { sectionLabel: "DeckCreator" });

  slide.addText(analysis.title, {
    x: 0.78,
    y: 0.9,
    w: 7.2,
    h: 1.05,
    fontFace: THEME.fonts.title,
    fontSize: THEME.text.heroTitle,
    bold: true,
    color: THEME.colors.ink,
    margin: 0,
    breakLine: false,
    fit: "shrink",
  });

  slide.addText("Automated marketing performance review generated from workbook data and rendered in PptxGenJS.", {
    x: 0.82,
    y: 2.02,
    w: 6.4,
    h: 0.52,
    fontFace: THEME.fonts.body,
    fontSize: 12,
    color: THEME.colors.accent,
    margin: 0,
    fit: "shrink",
  });

  addPanel(slide, 8.55, 0.82, 3.95, 5.55, {
    fill: THEME.colors.card,
    line: THEME.colors.line,
  });
  slide.addText("Render stack", {
    x: 8.9,
    y: 1.16,
    w: 2.4,
    h: 0.3,
    fontFace: THEME.fonts.body,
    fontSize: 10,
    bold: true,
    color: THEME.colors.muted,
    margin: 0,
  });
  slide.addText(
    [
      { text: "1. ", options: { bold: true, color: THEME.colors.ink } },
      { text: "Excel parsing and analysis" },
      { text: "\n2. ", options: { bold: true, color: THEME.colors.ink } },
      { text: "Executive insight generation" },
      { text: "\n3. ", options: { bold: true, color: THEME.colors.ink } },
      { text: "PptxGenJS deck assembly" },
      { text: "\n4. ", options: { bold: true, color: THEME.colors.ink } },
      { text: "Editable PowerPoint export" },
    ],
    {
      x: 8.9,
      y: 1.62,
      w: 3.1,
      h: 2.1,
      fontFace: THEME.fonts.body,
      fontSize: 13,
      color: THEME.colors.ink,
      margin: 0,
      breakLine: false,
      valign: "mid",
    },
  );

  slide.addText(buildReferenceSubtitle(referencePath), {
    x: 8.9,
    y: 4.65,
    w: 3.0,
    h: 0.85,
    fontFace: THEME.fonts.body,
    fontSize: 10,
    color: THEME.colors.muted,
    margin: 0,
    valign: "mid",
    fit: "shrink",
  });

  addFooter(slide, "Deck overview");
  addPageNumber(slide, 1);
}

function addKpiSlide(pptx, analysis) {
  const slide = createBaseSlide(pptx, { title: "Performance Overview", sectionLabel: "Overview" });
  const metrics = [
    { label: "Campaigns", value: analysis.kpis?.campaign_count || "-" },
    { label: "Revenue", value: analysis.kpis?.total_revenue || "-" },
    { label: "Investment", value: analysis.kpis?.total_investment || "-" },
    { label: "Average ROI", value: analysis.kpis?.average_roi || "-" },
  ];

  metrics.forEach((metric, index) => {
    const x = 0.78 + (index % 2) * 6.1;
    const y = 1.5 + Math.floor(index / 2) * 1.7;
    addMetricCard(slide, x, y, 5.55, 1.35, metric.label, metric.value);
  });

  slide.addText("Snapshot", {
    x: 0.82,
    y: 5.3,
    w: 1.2,
    h: 0.22,
    fontFace: THEME.fonts.body,
    fontSize: 9,
    bold: true,
    color: THEME.colors.muted,
    margin: 0,
  });
  slide.addText(
    "This slide is intentionally compact and executive-facing. It surfaces the workbook KPIs first, leaving channel and region detail for the following slides.",
    {
      x: 0.82,
      y: 5.55,
      w: 8.5,
      h: 0.75,
      fontFace: THEME.fonts.body,
      fontSize: 11,
      color: THEME.colors.ink,
      margin: 0,
      fit: "shrink",
    },
  );

  addFooter(slide, "Performance overview");
  addPageNumber(slide, 2);
}

function addTableSlide(pptx, title, rows, colTwoTitle, colThreeTitle) {
  if (!rows || rows.length === 0) {
    return;
  }

  const slide = createBaseSlide(pptx, { title, sectionLabel: "Performance" });
  const normalizedRows = rows.slice(0, 6).map((row) => [
    row.label ?? "",
    row.value_1 ?? "",
    row.value_2 ?? "",
  ]);
  const tableRows = [[
    headerCell("Segment"),
    headerCell(colTwoTitle || "Value"),
    headerCell(colThreeTitle || "Value"),
  ]];

  normalizedRows.forEach((row, index) => {
    tableRows.push(
      row.map((value) => bodyCell(String(value), index % 2 === 0 ? THEME.colors.card : THEME.colors.stripe))
    );
  });

  slide.addTable(tableRows, {
    x: 0.72,
    y: 1.45,
    w: 11.88,
    h: 4.85,
    margin: 0.08,
    border: { type: "solid", color: THEME.colors.line, pt: 1 },
    fontFace: THEME.fonts.body,
    colW: [5.45, 2.75, 3.68],
    rowH: 0.56,
    autoFit: false,
  });

  addFooter(slide, title);
  addPageNumber(slide, pptx._slides.length);
}

function addInsightSlide(pptx, title, items, options = {}) {
  if (!items || items.length === 0) {
    return;
  }

  const accentColor = options.accentColor || THEME.colors.accent;
  const slide = createBaseSlide(pptx, { title, sectionLabel: options.sectionLabel || "Insights" });

  addPanel(slide, 0.74, 1.38, 8.25, 4.95, {
    fill: THEME.colors.card,
    line: THEME.colors.line,
  });

  if (options.subtitle) {
    slide.addText(options.subtitle, {
      x: 9.24,
      y: 1.62,
      w: 3.0,
      h: 0.8,
      fontFace: THEME.fonts.body,
      fontSize: 10,
      color: THEME.colors.muted,
      margin: 0,
      fit: "shrink",
    });
  }

  const bullets = options.treatAsSummary
    ? [{ text: String(items[0]), options: { bullet: { indent: 0 } } }]
    : items.slice(0, 5).map((item) => ({ text: String(item), options: { bullet: { indent: 14 } } }));

  slide.addText(bullets, {
    x: 1.0,
    y: 1.8,
    w: 7.7,
    h: 4.1,
    fontFace: THEME.fonts.body,
    fontSize: options.treatAsSummary ? 14 : 13,
    color: THEME.colors.ink,
    breakLine: true,
    paraSpaceAfterPt: options.treatAsSummary ? 12 : 10,
    margin: 0,
    valign: "top",
    fit: "shrink",
  });

  addPanel(slide, 9.12, 2.18, 3.05, 1.45, {
    fill: THEME.colors.accentSoft,
    line: THEME.colors.line,
  });
  slide.addText("Narrative lens", {
    x: 9.42,
    y: 2.45,
    w: 1.8,
    h: 0.22,
    fontFace: THEME.fonts.body,
    fontSize: 9,
    bold: true,
    color: THEME.colors.muted,
    margin: 0,
  });
  slide.addText(
    options.treatAsSummary
      ? "Condense the workbook into one board-ready readout."
      : `Use ${title.toLowerCase()} to frame the story without overwhelming the deck.`,
    {
      x: 9.42,
      y: 2.78,
      w: 2.45,
      h: 0.62,
      fontFace: THEME.fonts.body,
      fontSize: 10.5,
      color: accentColor,
      margin: 0,
      fit: "shrink",
    },
  );

  addFooter(slide, title);
  addPageNumber(slide, pptx._slides.length);
}

function addMetricCard(slide, x, y, w, h, label, value) {
  addPanel(slide, x, y, w, h, {
    fill: THEME.colors.card,
    line: THEME.colors.line,
  });
  slide.addText(label, {
    x: x + 0.28,
    y: y + 0.22,
    w: w - 0.5,
    h: 0.2,
    fontFace: THEME.fonts.body,
    fontSize: 9,
    bold: true,
    color: THEME.colors.muted,
    margin: 0,
  });
  slide.addText(String(value), {
    x: x + 0.28,
    y: y + 0.52,
    w: w - 0.5,
    h: 0.42,
    fontFace: THEME.fonts.title,
    fontSize: THEME.text.metric,
    bold: true,
    color: THEME.colors.ink,
    margin: 0,
    fit: "shrink",
  });
}

function createBaseSlide(pptx, options = {}) {
  const slide = pptx.addSlide();
  slide.background = { color: THEME.colors.canvas };

  slide.addShape(SHAPE_TYPES.line, {
    x: 0.7,
    y: 0.72,
    w: 12.0,
    h: 0,
    line: { color: THEME.colors.line, pt: 1 },
  });

  if (options.sectionLabel) {
    slide.addText(options.sectionLabel.toUpperCase(), {
      x: 0.78,
      y: 0.25,
      w: 1.8,
      h: 0.2,
      fontFace: THEME.fonts.body,
      fontSize: THEME.text.eyebrow,
      bold: true,
      color: THEME.colors.muted,
      margin: 0,
      charSpace: 1.2,
    });
  }

  if (options.title) {
    slide.addText(options.title, {
      x: 0.78,
      y: 0.92,
      w: 7.4,
      h: 0.52,
      fontFace: THEME.fonts.title,
      fontSize: THEME.text.slideTitle,
      bold: true,
      color: THEME.colors.ink,
      margin: 0,
      fit: "shrink",
    });
  }

  return slide;
}

function addPanel(slide, x, y, w, h, { fill, line }) {
  slide.addShape(SHAPE_TYPES.rect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: { color: line, pt: 1 },
    fill: { color: fill },
  });
}

function addFooter(slide, label) {
  slide.addText(label, {
    x: 0.78,
    y: THEME.spacing.footerY,
    w: 2.8,
    h: 0.18,
    fontFace: THEME.fonts.body,
    fontSize: 8,
    color: THEME.colors.muted,
    margin: 0,
  });
}

function addPageNumber(slide, pageNumber) {
  slide.addText(String(pageNumber), {
    x: 12.1,
    y: THEME.spacing.footerY - 0.02,
    w: 0.45,
    h: 0.18,
    align: "right",
    fontFace: THEME.fonts.body,
    fontSize: 8,
    color: THEME.colors.muted,
    margin: 0,
  });
}

function addSectionSlide(pptx, title, subtitle) {
  const slide = createBaseSlide(pptx, { sectionLabel: "Section" });
  slide.addText(title, {
    x: 0.9,
    y: 2.0,
    w: 8.6,
    h: 0.8,
    fontFace: THEME.fonts.title,
    fontSize: 26,
    bold: true,
    color: THEME.colors.ink,
    margin: 0,
  });
  slide.addText(subtitle, {
    x: 0.94,
    y: 2.95,
    w: 6.2,
    h: 0.5,
    fontFace: THEME.fonts.body,
    fontSize: 12,
    color: THEME.colors.accent,
    margin: 0,
  });
  addFooter(slide, title);
  addPageNumber(slide, pptx._slides.length);
}

function addChartSlide(pptx, title, categories, values) {
  const slide = createBaseSlide(pptx, { title, sectionLabel: "Chart" });
  slide.addChart(CHART_TYPES.bar, [{ name: "Series 1", labels: categories, values }], {
    x: 0.9,
    y: 1.5,
    w: 11.2,
    h: 4.8,
    catAxisLabelFontFace: THEME.fonts.body,
    valAxisLabelFontFace: THEME.fonts.body,
    chartColors: [THEME.colors.accent],
    showLegend: false,
    showTitle: false,
  });
  addFooter(slide, title);
  addPageNumber(slide, pptx._slides.length);
}

function buildReferenceSubtitle(referencePath) {
  if (!referencePath) {
    return THEME.meta.designSummary
      ? `Theme direction: ${THEME.meta.designSummary}`
      : "No reference file was provided. The deck uses a researched built-in presentation system.";
  }
  const referenceName = path.basename(referencePath);
  return `Reference input: ${referenceName}. The slide engine uses a consistent generated theme rather than mutating the uploaded file directly.`;
}

function createTheme(themeInput = {}) {
  const colors = themeInput.colors || {};
  const fonts = themeInput.fonts || {};
  return {
    ...DEFAULT_THEME,
    colors: {
      ...DEFAULT_THEME.colors,
      canvas: sanitizeColor(colors.canvas, DEFAULT_THEME.colors.canvas),
      ink: sanitizeColor(colors.ink, DEFAULT_THEME.colors.ink),
      muted: sanitizeColor(colors.muted, DEFAULT_THEME.colors.muted),
      accent: sanitizeColor(colors.accent, DEFAULT_THEME.colors.accent),
      accentSoft: sanitizeColor(colors.accent_soft || colors.accentSoft, DEFAULT_THEME.colors.accentSoft),
      line: sanitizeColor(colors.line, DEFAULT_THEME.colors.line),
      card: sanitizeColor(colors.card, DEFAULT_THEME.colors.card),
      stripe: sanitizeColor(colors.stripe, DEFAULT_THEME.colors.stripe),
      danger: sanitizeColor(colors.danger, DEFAULT_THEME.colors.danger),
    },
    fonts: {
      ...DEFAULT_THEME.fonts,
      title: fonts.title || DEFAULT_THEME.fonts.title,
      body: fonts.body || DEFAULT_THEME.fonts.body,
      mono: fonts.mono || fonts.body || DEFAULT_THEME.fonts.mono,
    },
    meta: {
      themeName: themeInput.theme_name || "DeckCreator System",
      designSummary: themeInput.design_summary || "",
    },
  };
}

function sanitizeColor(value, fallback) {
  if (typeof value !== "string") {
    return fallback;
  }
  const normalized = value.replace("#", "").trim().toUpperCase();
  return /^[0-9A-F]{6}$/.test(normalized) ? normalized : fallback;
}

function buildSampleHeaders(sampleRows) {
  if (!sampleRows || sampleRows.length === 0) {
    return ["Column A", "Column B"];
  }
  const keys = Object.keys(sampleRows[0]).slice(0, 4);
  if (keys.length === 1) {
    return [keys[0], "Value"];
  }
  if (keys.length === 2) {
    return [keys[0], keys[1]];
  }
  return [keys[1] || "Value", keys[2] || "Value"];
}

function buildSampleRows(sampleRows) {
  if (!sampleRows || sampleRows.length === 0) {
    return [];
  }
  return sampleRows.slice(0, 5).map((row) => {
    const keys = Object.keys(row).slice(0, 3);
    if (keys.length >= 3) {
      return {
        label: String(row[keys[0]] ?? ""),
        value_1: String(row[keys[1]] ?? ""),
        value_2: String(row[keys[2]] ?? ""),
      };
    }
    if (keys.length === 2) {
      return {
        label: String(row[keys[0]] ?? ""),
        value_1: String(row[keys[1]] ?? ""),
        value_2: "",
      };
    }
    return {
      label: String(row[keys[0]] ?? ""),
      value_1: "",
      value_2: "",
    };
  });
}

function headerCell(text) {
  return {
    text,
    options: {
      bold: true,
      color: THEME.colors.ink,
      fill: THEME.colors.accentSoft,
      align: "left",
      valign: "mid",
      margin: 0.08,
      fontFace: THEME.fonts.body,
      fontSize: THEME.text.table,
    },
  };
}

function bodyCell(text, fill) {
  return {
    text,
    options: {
      color: THEME.colors.ink,
      fill,
      align: "left",
      valign: "mid",
      margin: 0.08,
      fontFace: THEME.fonts.body,
      fontSize: THEME.text.table,
    },
  };
}

function ensureDirectory(directoryPath) {
  fs.mkdirSync(directoryPath, { recursive: true });
}

main().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
