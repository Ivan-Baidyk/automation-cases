import express from "express";
import crypto from "crypto";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;
const GOTENBERG_URL = process.env.GOTENBERG_URL || "http://gotenberg:3000";
const PUBLIC_BASE = process.env.PUBLIC_BASE || ("http://localhost:" + PORT);
const PDF_DIR = path.join(__dirname, "pdf");

fs.mkdirSync(PDF_DIR, { recursive: true });

app.use(express.json({ limit: "30mb" }));
app.use(express.urlencoded({ extended: true, limit: "30mb" }));
app.use(express.text({ type: "text/html", limit: "30mb" }));
app.use("/pdf", express.static(PDF_DIR, { index: false }));

app.get("/health", (req, res) => res.json({ status: "ok", gotenberg: GOTENBERG_URL }));

app.post("/convert", async (req, res) => {
  try {
    // HTML может прийти: JSON {html}, form-urlencoded html=..., либо raw text/html
    let html = null;
    if (req.body && typeof req.body === "object" && req.body.html) html = req.body.html;
    else if (typeof req.body === "string") html = req.body;

    if (!html) return res.status(400).json({ error: "missing html" });

    const base = String((req.body && req.body.filename) || "document")
      .replace(/[^\w\-]+/g, "_")
      .slice(0, 80) || "document";
    const id = Date.now() + "-" + crypto.randomBytes(4).toString("hex");
    const pdfName = base + "-" + id + ".pdf";

    const form = new FormData();
    form.append("files", new Blob([html], { type: "text/html" }), "index.html");
    form.append("printBackground", "true");
    form.append("preferCssPageSize", "true");

    const r = await fetch(GOTENBERG_URL + "/forms/chromium/convert/html", {
      method: "POST",
      body: form,
    });

    if (!r.ok) {
      const detail = (await r.text()).slice(0, 800);
      return res.status(r.status).json({ error: "gotenberg error", detail });
    }

    const buf = Buffer.from(await r.arrayBuffer());
    fs.writeFileSync(path.join(PDF_DIR, pdfName), buf);

    return res.json({
      ok: true,
      url: PUBLIC_BASE.replace(/\/$/, "") + "/pdf/" + pdfName,
      filename: pdfName,
      size: buf.length,
    });
  } catch (e) {
    return res.status(500).json({ error: e && e.message ? e.message : String(e) });
  }
});

app.listen(PORT, () => console.log("html2pdf-api listening on :" + PORT + " -> " + GOTENBERG_URL));
