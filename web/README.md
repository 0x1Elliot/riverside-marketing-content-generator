# Riverside Books Marketing Generator web MVP

This React + Vite interface sends catalog JSON and optional reader-context JSON to the FastAPI `POST /generate` endpoint. It displays the selected reader-engagement message, legacy generated drafts, rejected records, and validation diagnostics.

## Run locally

From this directory:

```bash
npm install
cp .env.example .env.local
npm run dev
```

`.env.example` points to the verified Render API. Override `VITE_API_BASE_URL` in `.env.local` when using another backend.

Load the sample catalog to see the engagement MVP. Clear the optional reader
context field to use the original catalog-only request shape.

Start the backend from the project root with:

```bash
uvicorn riverside_marketing.api:app --app-dir src --reload
```

## Deployment preparation

For Vercel, set the project root to `web`, keep the build command as `npm run build`, keep the output directory as `dist`, and define `VITE_API_BASE_URL` as the hosted FastAPI URL. Production builds fail clearly at request time if that variable is missing.

The repository root contains `render.yaml` for a low-cost Render FastAPI web service. Set `RIVERSIDE_ALLOWED_ORIGINS` in the Render dashboard to the deployed frontend origin, then use the service's HTTPS `onrender.com` URL as `VITE_API_BASE_URL` in Vercel.
