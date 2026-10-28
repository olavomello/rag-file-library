# ADR 0009: Optional local OCR for scanned PDFs and images

## Status

Accepted — 2026-10-28. Revisits the "No OCR in V1" stance in ADR-0003.

## Context

ADR-0003 deliberately shipped without OCR: scanned PDFs with no text layer were
reported, not processed, and image files were unsupported. Users need to index
image-only documents (scanned PDFs, photos, screenshots) without sending anything to a
cloud service, on the same local-first, CPU-only, integrated-GPU target as the rest of
the app.

## Decision

Add local OCR behind a port, on by default (it can be turned off).

- **Engine: RapidOCR (`rapidocr-onnxruntime`).** Runs on CPU via ONNX Runtime with no
  CUDA dependency and no external system binary to install, and works offline — unlike
  Tesseract (needs a system binary + language packs) or EasyOCR (heavy PyTorch). The
  engine is heavy to construct, so it is lazily initialised on first use and only when
  OCR is enabled.
- **`OcrProvider` port** (`application/ports/ocr.py`) with a `RapidOcrProvider`
  infrastructure adapter, so the engine stays replaceable and tests use a fake.
- **`ocr_enabled` (default `true`).** It is a normal overridable setting (`OCR_ENABLED`,
  `PATCH /settings`); changing it sets `requires_restart` because parsers are built at
  startup. With OCR off, behaviour is identical to ADR-0003 (scanned PDF →
  `NoExtractableTextError`). `GET /settings` returns the effective-after-restart view
  (saved overrides applied), so a saved toggle is reflected immediately even though it
  takes effect on the next restart.
- **Two entry points:** an `ImageParser` for PNG/JPG/JPEG/TIFF/BMP/WEBP (validated by
  magic bytes), and an OCR fallback in `PdfParser` that rasterises only the pages with no
  text layer. The fast text path for normal PDFs is unchanged. OCR runs inside the
  existing background indexing worker, so uploads stay responsive.
- **Safety unchanged:** OCR'd text is still treated as untrusted document content and
  flows through the same grounding/prompt-injection rules.

## Consequences

- Scanned PDFs and images can be indexed, searched, and used in RAG chat — fully local.
- OCR on CPU is noticeably slower than text extraction and its accuracy depends on scan
  quality; this is acceptable for an opt-in feature and documented as a limitation.
- A new dependency (`rapidocr-onnxruntime`) is added; the committed `backend/openapi.json`
  now exposes `ocr_enabled` (contract test enforces it). The OCR language set is not yet
  configurable (future work).
