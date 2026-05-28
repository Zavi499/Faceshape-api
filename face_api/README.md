# Face Analysis FastAPI API

This project provides a production-ready FastAPI API that accepts a single face image, analyzes facial proportions and features, saves the original plus highlighted mesh image, and automatically deletes stored images after the configured TTL. In addition to the original full-analysis endpoint, the API now includes dedicated endpoints for symmetry, lips, nose, eyes, golden-ratio breakdowns, and DNN-based age estimation.

## Install

```bash
cd face_api
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

## Docs

Open `http://localhost:8000/docs`

## Deploy On Coolify

This app is ready to deploy through Coolify using the Dockerfile build pack. The FastAPI server listens inside the container on port `8000`.

### 1. Push The Code To Git

Push this repository to GitHub, GitLab, Bitbucket, or another Git provider connected to Coolify.

Make sure the deployable app directory is `face_api/`, because that is where `Dockerfile`, `main.py`, and `requirements.txt` live.

### 2. Create The App In Coolify

In the Coolify dashboard:

1. Open your project.
2. Click `New Resource`.
3. Choose your Git source.
4. Select this repository and branch.
5. Choose `Dockerfile` as the build pack.

Use these settings:

```text
Base Directory: /face_api
Dockerfile Location: /Dockerfile
Port Exposes: 8000
```

Coolify often defaults the exposed app port to `3000`, so change it to `8000`.

### 2.1 Add Environment Variables

To allow browser requests only from the frontend domain, add this environment variable in Coolify:

```text
ALLOWED_ORIGINS=https://facesanalyzer.com,https://www.facesanalyzer.com
```

The API enforces this for `/analyze`, specialized analysis endpoints, and `/image/{filename}`. Requests from other browser origins receive HTTP `403`.

### 3. Add Domain

In the app settings, set your domain:

```text
https://api.yourdomain.com
```

Enable HTTPS/force HTTPS if your DNS is already pointing to the VPS.

### 4. Optional Persistent Storage

The API saves temporary original and highlighted images in `/app/outputs` inside the container. They auto-delete after `IMAGE_TTL_MINUTES`, so persistent storage is optional.

If you want images to survive app restarts until their TTL expires, add a Coolify storage volume:

```text
Mount Path: /app/outputs
```

### 5. Deploy And Test

Click `Deploy`, then open:

```text
https://api.yourdomain.com/docs
```

Test with curl:

```bash
curl -X POST "https://api.yourdomain.com/analyze" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

If you do not have a domain yet, Coolify may give you a generated URL. Use that URL in place of `https://api.yourdomain.com`.

## POST /analyze

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

## Specialized POST Endpoints

All specialized endpoints use the same `multipart/form-data` upload format with the `file` field.

### POST /analyze/symmetry

```bash
curl -X POST "http://localhost:8000/analyze/symmetry" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

### POST /analyze/lips

```bash
curl -X POST "http://localhost:8000/analyze/lips" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

### POST /analyze/nose

```bash
curl -X POST "http://localhost:8000/analyze/nose" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

### POST /analyze/age

```bash
curl -X POST "http://localhost:8000/analyze/age" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

### POST /analyze/eyes

```bash
curl -X POST "http://localhost:8000/analyze/eyes" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

### POST /analyze/golden-ratio

```bash
curl -X POST "http://localhost:8000/analyze/golden-ratio" \
  -H "accept: application/json" \
  -F "file=@sample.jpg"
```

## GET /image/{filename}

```bash
curl -X GET "http://localhost:8000/image/api_20260404_120000_ab12cd34.jpg" \
  --output downloaded.jpg
```

## DELETE /image/{filename}

```bash
curl -X DELETE "http://localhost:8000/image/api_20260404_120000_ab12cd34.jpg"
```

## Privacy And TTL

Stored images are written to `./outputs` inside the `face_api` directory. They expire after `IMAGE_TTL_MINUTES` minutes, which defaults to 30. A background APScheduler job runs every 5 minutes to delete expired files automatically, and the API response includes the exact `expires_at` timestamp plus the privacy note for each successful analysis.

## Age Model Note

The age endpoint uses a dedicated OpenCV DNN model rather than ratio-based heuristics. The required model files are downloaded automatically into `./models` the first time the age estimator is initialized.

## Security Note

The API uses an origin guard and CORS headers so browser requests are accepted only from `facesanalyzer.com` by default. This protects normal website usage, but `Origin` headers can be spoofed by non-browser clients. For private or paid production access, add API-key authentication or user authentication in addition to the origin restriction.
