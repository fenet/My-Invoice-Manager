from datetime import date
from sqlalchemy import select, func, extract
from sqlalchemy.orm import Session
from models import Company, Client, Invoice, InvoiceItem
from settings import COMPANY_DEFAULTS, INVOICE_NUMBER_FORMAT, RESET_SEQUENCE_EACH_YEAR

def seed_company(db: Session):
    existing = db.execute(select(Company)).scalars().first()
    if not existing:
        comp = Company(**COMPANY_DEFAULTS)
        db.add(comp)
        db.commit()
        db.refresh(comp)
        return comp
    return existing

def list_clients(db: Session):
    return db.execute(select(Client).order_by(Client.company_name)).scalars().all()

def create_client(db: Session, company_name: str, address: str, uid: str | None):
    cl = Client(company_name=company_name, address=address, uid=uid or None)
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl

def get_company(db: Session) -> Company:
    return db.execute(select(Company)).scalars().first()

def get_client(db: Session, client_id: int) -> Client:
    return db.get(Client, client_id)

def next_invoice_number(db: Session, today: date):
    year = today.year
    if RESET_SEQUENCE_EACH_YEAR:
        last = db.execute(
            select(func.max(Invoice.year_seq)).where(extract('year', Invoice.date) == year)
        ).scalar() or 0
        seq = last + 1
    else:
        last = db.execute(select(func.count(Invoice.id))).scalar() or 0
        seq = last + 1
    number = INVOICE_NUMBER_FORMAT.format(year=year, seq=seq)
    return number, seq

def create_invoice_with_items(db: Session, *, client_id: int, service_period: str | None, objekt: str | None, date_: date, items: list[dict], city: str | None, reverse_charge: bool = True):
    company = get_company(db)
    client = get_client(db, client_id)
    num, seq = next_invoice_number(db, date_)
    inv = Invoice(
        number=num,
        date=date_,
        service_period=service_period or None,
        objekt=objekt or None,
        client_id=client.id,
        company_id=company.id,
        city=city,
        reverse_charge=reverse_charge,
        year_seq=seq
    )
    total = 0
    db.add(inv)
    db.flush()
    for it in items:
        # compute net if not provided
        schluessel = float(it.get("schluessel") or 0)
        unit_price = float(it.get("unit_price") or 0)
        net = float(it.get("net") or schluessel * unit_price)
        total += net
        db.add(InvoiceItem(
            invoice_id=inv.id,
            title=it.get("title") or "",
            termin=it.get("termin") or None,
            schluessel=schluessel or None,
            unit_price=unit_price,
            net=net
        ))
    inv.total_net = round(total, 2)
    db.commit()
    db.refresh(inv)
    return inv

def get_invoice(db: Session, invoice_id: int) -> Invoice:
    return db.get(Invoice, invoice_id)

def list_invoices(db: Session):
    return db.execute(select(Invoice).order_by(Invoice.date.desc(), Invoice.number.desc())).scalars().all()
