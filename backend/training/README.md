# ClaimBuster Claim-Detector — Training

Replaces the hand-coded claim heuristic with a trained binary classifier
(check-worthy vs not), so claims like "best university in the world" get caught.

## Train (Kaggle, free GPU)
1. New Kaggle notebook → upload `ClaimBuster_Train.ipynb` → Accelerator: **GPU T4**.
2. **Add Data** → search **"claimbuster"** → add a ClaimBuster dataset.
3. Run all. Trained model saves to `/kaggle/working/claimbuster-detector`.
4. Either push to the HF Hub (cell 7) or download the folder from Kaggle output.

## Plug it into the backend
Set one environment variable before starting the backend:
- Hub:   `CLAIM_MODEL=your-username/claimbuster-detector`
- Local: put the folder in `backend/` and set `CLAIM_MODEL=./claimbuster-detector`

PowerShell example:
```powershell
$env:CLAIM_MODEL = "./claimbuster-detector"
python -m uvicorn main:app --port 7860
```

No env var = the app keeps using the heuristic. The trained model is a drop-in
upgrade, not a requirement. Each claim now reports `method: "model"` or `"heuristic"`.
