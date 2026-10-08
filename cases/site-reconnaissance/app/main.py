from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import scrapalyser
import subprocess
import json
import tempfile
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Site Analyzer", version="1.0.0")


class AnalyzeRequest(BaseModel):
    url: str
    deep: bool = False          # priнуditelno zapuskat api-recon
    diagnostics: bool = False   # zapuskat caniscrape dlya glubokoy diagnostiki


class AnalyzeResponse(BaseModel):
    url: str
    scrapalyser: dict | None = None
    api_recon: dict | None = None
    caniscrape: dict | None = None
    error: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


def _valid_url(url: str) -> bool:
    return url.lower().startswith(("http://", "https://"))


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not _valid_url(req.url):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")

    result = {
        "url": req.url,
        "scrapalyser": None,
        "api_recon": None,
        "caniscrape": None,
        "error": None,
    }

    # Etap 1: bystryy skan scrapalyser
    try:
        logger.info(f"scrapalyser: {req.url}")
        report = scrapalyser.scan(url=req.url, output="json", engine="curl")
        if isinstance(report, str):
            report = json.loads(report)
        result["scrapalyser"] = report
    except Exception as e:
        result["scrapalyser"] = {"error": str(e)}
        logger.error(f"scrapalyser failed: {e}")

    # Etap 2: api-recon (po trebovaniyu)
    sa = result["scrapalyser"] or {}
    antibot = sa.get("antibot")
    antibot_detected = bool(antibot.get("detected")) if isinstance(antibot, dict) else bool(antibot)
    should_recon = (
        req.deep
        or bool(sa.get("js_required"))
        or antibot_detected
    )

    if should_recon:
        try:
            logger.info(f"api-recon: {req.url}")
            with tempfile.TemporaryDirectory() as tmpdir:
                proc = subprocess.run(
                    ["api-recon", req.url, "--depth", "1",
                     "--max-pages", "20", "--formats", "json",
                     "--out", tmpdir, "--no-respect-robots", "--force"],
                    capture_output=True, text=True, timeout=180,
                )
                report_path = os.path.join(tmpdir, "report.json")
                if os.path.exists(report_path):
                    with open(report_path) as f:
                        result["api_recon"] = json.load(f)
                else:
                    files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
                    if files:
                        with open(os.path.join(tmpdir, files[0])) as f:
                            result["api_recon"] = json.load(f)
                    else:
                        result["api_recon"] = {
                            "exit_code": proc.returncode,
                            "stderr": proc.stderr[-2000:],
                        }
        except subprocess.TimeoutExpired:
            result["api_recon"] = {"error": "timeout after 180s"}
        except Exception as e:
            result["api_recon"] = {"error": str(e)}

    # Etap 3: caniscrape (glubokaya diagnostika)
    if req.diagnostics:
        try:
            logger.info(f"caniscrape: {req.url}")
            proc = subprocess.run(
                ["caniscrape", "scan", req.url, "--impersonate", "--find-all"],
                capture_output=True, text=True, timeout=120,
            )
            result["caniscrape"] = {
                "stdout": proc.stdout[-8000:],
                "stderr": proc.stderr[-2000:],
            }
        except subprocess.TimeoutExpired:
            result["caniscrape"] = {"error": "timeout after 120s"}
        except Exception as e:
            result["caniscrape"] = {"error": str(e)}

    return result
