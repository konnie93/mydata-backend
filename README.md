# myDATA Monitor — Backend API

Python/FastAPI backend που συνδέεται με το myDATA API της ΑΑΔΕ.

## Deployment στο Railway

### 1. Ανέβασε στο GitHub
```bash
git init
git add .
git commit -m "initial"
git remote add origin https://github.com/ΧΡΗΣΤΗΣ/mydata-backend.git
git push -u origin main
```

### 2. Railway setup
1. Πήγαινε στο railway.app → New Project → Deploy from GitHub
2. Επέλεξε το repo `mydata-backend`
3. Πήγαινε στο **Variables** και πρόσθεσε:

| Variable | Τιμή |
|---|---|
| `MYDATA_USER_ID` | το username σου στο myDATA |
| `MYDATA_SUBSCRIPTION_KEY` | το subscription key από το myDATA portal |
| `MYDATA_USE_DEV` | `true` για δοκιμές, `false` για παραγωγή |

### 3. Παίρνεις URL
Μετά το deploy παίρνεις κάτι τύπου:
`https://mydata-backend-production.up.railway.app`

## API Endpoints

### `GET /invoices`
Παράμετροι:
- `date_from` — π.χ. `2026-07-13`
- `date_to` — π.χ. `2026-07-13`
- `entity_vat` — ΑΦΜ εταιρείας (για λογιστήρια)

Παράδειγμα:
```
GET /invoices?date_from=2026-07-13&date_to=2026-07-13&entity_vat=099123456
```

### `GET /health`
Έλεγχος ότι τρέχει ο server.
