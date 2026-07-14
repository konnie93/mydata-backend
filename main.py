from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import xmltodict
import os
from datetime import date

app = FastAPI(title="myDATA Monitor API")

# CORS — επιτρέπει κλήσεις από τον browser (Netlify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# myDATA endpoints
MYDATA_URL = "https://mydatapi.aade.gr/myDATA"
MYDATA_DEV_URL = "https://mydataapidev.aade.gr/myDATA"

def get_credentials():
    """Παίρνει credentials από environment variables (Railway)"""
    user_id = os.getenv("MYDATA_USER_ID")
    sub_key = os.getenv("MYDATA_SUBSCRIPTION_KEY")
    use_dev = os.getenv("MYDATA_USE_DEV", "false").lower() == "true"
    
    if not user_id or not sub_key:
        raise HTTPException(
            status_code=500,
            detail="Δεν έχουν οριστεί τα MYDATA_USER_ID / MYDATA_SUBSCRIPTION_KEY"
        )
    
    base_url = MYDATA_DEV_URL if use_dev else MYDATA_URL
    headers = {
        "aade-user-id": user_id,
        "Ocp-Apim-Subscription-Key": sub_key
    }
    return base_url, headers


@app.get("/")
def root():
    return {"status": "ok", "service": "myDATA Monitor API"}


@app.get("/invoices")
async def get_invoices(
    date_from: str = None,
    date_to: str = None,
    entity_vat: str = None
):
    """
    Τραβάει παραστατικά από myDATA.
    date_from / date_to: μορφή YYYY-MM-DD (προεπιλογή: σήμερα)
    entity_vat: ΑΦΜ τρίτης εταιρείας (για λογιστήρια που κοιτάνε πελάτες τους)
    """
    base_url, headers = get_credentials()
    
    today = date.today().strftime("%Y-%m-%d")
    df = date_from or today
    dt = date_to or today

    params = {
        "dateFrom": df,
        "dateTo": dt,
    }
    
    if entity_vat:
        params["entityVatNumber"] = entity_vat

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{base_url}/RequestMyIncome",
                headers=headers,
                params=params
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Δεν ήταν δυνατή η σύνδεση με myDATA: {e}")

    # Μετατροπή XML → JSON
    try:
        data = xmltodict.parse(resp.text)
    except Exception:
        raise HTTPException(status_code=502, detail="Μη αναμενόμενη απάντηση από myDATA")

    invoices_raw = (
        data.get("RequestedDoc", {})
            .get("invoicesDoc", {})
            .get("invoice", [])
    )

    # Κανονικοποίηση σε λίστα (αν είναι μόνο ένα, έρχεται ως dict)
    if isinstance(invoices_raw, dict):
        invoices_raw = [invoices_raw]

    # Μορφοποίηση για το dashboard
    result = []
    for inv in invoices_raw:
        header = inv.get("invoiceHeader", {})
        result.append({
            "mark":        inv.get("mark"),
            "uid":         inv.get("uid"),
            "date":        header.get("issueDate"),
            "type":        header.get("invoiceType"),
            "series":      header.get("series"),
            "aa":          header.get("aa"),
            "currency":    header.get("currency", "EUR"),
            "issuer_vat":  inv.get("issuer", {}).get("vatNumber"),
            "counterpart_vat": inv.get("counterpart", {}).get("vatNumber"),
            "total_value": inv.get("invoiceSummary", {}).get("totalGrossValue"),
            "mydata":      "ok" if inv.get("mark") else "fail",
        })

    return {
        "count": len(result),
        "date_from": df,
        "date_to": dt,
        "invoices": result
    }


@app.get("/health")
def health():
    return {"status": "ok"}
