from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from weasyprint import HTML, CSS

import io
from datetime import date

# Local imports
from database import Base, engine, get_db
from models import Company, Client, Invoice, InvoiceItem
from crud import (
    seed_company,
    list_clients,
    list_invoices,
    create_client,
    get_client,
    get_company,
    get_invoice,
    create_invoice_with_items
)
from auth import verify_credentials, login_required

# ---------- APP SETUP ----------
app = FastAPI(title="My Invoice Manager")
app.add_middleware(SessionMiddleware, secret_key="1234567")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja templates
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(['html', 'xml'])
)
templates = Jinja2Templates(directory="templates")


# ---------- STARTUP ----------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed_company(db)


# ---------- HELPER ----------
def render(template_name: str, **kwargs):
    """Helper wrapper for Jinja TemplateResponse."""
    request = kwargs.get("request")
    return templates.TemplateResponse(template_name, kwargs)


# ---------- LOGIN ----------
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if verify_credentials(username, password):
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


# ---------- HOME ----------
@app.get("/", response_class=HTMLResponse)
@login_required
async def index(request: Request, db: Session = Depends(get_db)):
    invoices = list_invoices(db)
    clients = list_clients(db)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "invoices": invoices, "clients": clients}
    )


# ---------- CLIENTS ----------
@app.get("/clients/new", response_class=HTMLResponse)
def new_client(request: Request):
    return render("new_client.html", request=request)


@app.post("/clients/create")
def create_client_post(
    company_name: str = Form(...),
    address: str = Form(...),
    uid: str | None = Form(None),
    db: Session = Depends(get_db)
):
    create_client(db, company_name=company_name, address=address, uid=uid)
    return RedirectResponse(url="/", status_code=303)


@app.get("/clients/{client_id}/edit", response_class=HTMLResponse)
def edit_client(client_id: int, request: Request, db: Session = Depends(get_db)):
    client = get_client(db, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    return render("edit_client.html", request=request, client=client)


@app.post("/clients/{client_id}/update")
def update_client_post(
    client_id: int,
    company_name: str = Form(...),
    address: str = Form(...),
    uid: str | None = Form(None),
    db: Session = Depends(get_db)
):
    client = get_client(db, client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    client.company_name = company_name
    client.address = address
    client.uid = uid
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/clients/{client_id}/delete")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = get_client(db, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    db.delete(client)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# ---------- INVOICES ----------
INVOICE_CITY = "Berlin"  # default city if none given

@app.get("/invoices/new", response_class=HTMLResponse)
def new_invoice(request: Request, db: Session = Depends(get_db)):
    clients = list_clients(db)
    company = get_company(db)
    return render(
        "new_invoice.html",
        request=request,
        clients=clients,
        company=company,
        today=date.today(),
        default_city=INVOICE_CITY
    )


@app.post("/invoices/create")
def create_invoice_post(
    client_id: int = Form(...),
    service_period: str | None = Form(None),
    objekt: str | None = Form(None),
    date_str: str = Form(...),
    city: str | None = Form(None),
    reverse_charge: bool = Form(False),
    # items arrays
    item_title: list[str] = Form([]),
    item_termin: list[str] = Form([]),
    item_schluessel: list[str] = Form([]),
    item_unit_price: list[str] = Form([]),
    item_net: list[str] = Form([]),
    db: Session = Depends(get_db)
):
    d = date.fromisoformat(date_str)
    items = []
    n = max(len(item_title), len(item_termin), len(item_schluessel), len(item_unit_price), len(item_net))

    for i in range(n):
        title = item_title[i] if i < len(item_title) else ""
        termin = item_termin[i] if i < len(item_termin) else None
        schluessel = item_schluessel[i] if i < len(item_schluessel) else ""
        unit_price = item_unit_price[i] if i < len(item_unit_price) else ""
        net = item_net[i] if i < len(item_net) else ""

        if title or termin or schluessel or unit_price or net:
            items.append({
                "title": title,
                "termin": termin,
                "schluessel": schluessel or 0,
                "unit_price": unit_price or 0,
                "net": net or None
            })

    inv = create_invoice_with_items(
        db,
        client_id=client_id,
        service_period=service_period,
        objekt=objekt,
        date_=d,
        items=items,
        city=city,
        reverse_charge=reverse_charge
    )
    return RedirectResponse(url=f"/invoices/{inv.id}", status_code=303)


@app.get("/invoices/{invoice_id}", response_class=HTMLResponse)
def show_invoice(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return render("invoice_show.html", request=request, invoice=inv)


@app.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")

    html_content = templates.get_template("invoice_pdf.html").render(invoice=inv)
    pdf_io = io.BytesIO()
    HTML(string=html_content, base_url=".").write_pdf(
        pdf_io, stylesheets=[CSS(filename="static/css/invoice.css")]
    )
    pdf_io.seek(0)

    headers = {"Content-Disposition": f'attachment; filename="invoice_{inv.number}.pdf"'}
    return StreamingResponse(pdf_io, media_type="application/pdf", headers=headers)


@app.post("/invoices/{invoice_id}/delete")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    db.delete(inv)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/invoices/{invoice_id}/edit", response_class=HTMLResponse)
def edit_invoice(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return render("edit_invoice.html", request=request, invoice=inv)


@app.post("/invoices/{invoice_id}/update")
def update_invoice(
    invoice_id: int,
    service_period: str = Form(...),
    reverse_charge: bool = Form(False),
    item_titles: list[str] = Form([]),
    item_schluessel: list[str] = Form([]),
    item_unit_price: list[str] = Form([]),
    item_netto: list[str] = Form([]),
    db: Session = Depends(get_db)
):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")

    # update invoice header
    inv.service_period = service_period
    inv.reverse_charge = reverse_charge

    # delete old items
    inv.items.clear()

    # recreate items
    for title, schluessel, unit_price, netto in zip(item_titles, item_schluessel, item_unit_price, item_netto):
        s = float(schluessel or 0)
        u = float(unit_price or 0)
        n = float(netto or s * u)
        inv.items.append(
            InvoiceItem(
                title=title,
                schluessel=s,
                unit_price=u,
                net=n
            )
        )

    db.commit()
    db.refresh(inv)
    return RedirectResponse(url="/", status_code=303)

