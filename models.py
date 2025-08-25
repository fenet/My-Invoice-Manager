from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date
from database import Base

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    address: Mapped[str]
    uid: Mapped[str | None]
    employer_no: Mapped[str | None]
    email: Mapped[str | None]
    website: Mapped[str | None]
    reverse_charge_note: Mapped[str | None]

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str]
    address: Mapped[str]
    uid: Mapped[str | None]

    invoices = relationship("Invoice", back_populates="client")

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str]
    date: Mapped[date]
    service_period: Mapped[str | None]
    objekt: Mapped[str | None]
    city: Mapped[str | None]
    year_seq: Mapped[int] = mapped_column(default=0)  # sequence within year
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    total_net: Mapped[Numeric] = mapped_column(Numeric(12,2), default=0)
    reverse_charge: Mapped[bool] = mapped_column(Boolean, default=True)

    client = relationship("Client", back_populates="invoices")
    company = relationship("Company")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    title: Mapped[str]
    termin: Mapped[str | None]  # dates/description
    schluessel: Mapped[float | None]  # hours/units
    unit_price: Mapped[Numeric] = mapped_column(Numeric(12,2), default=0)
    net: Mapped[Numeric] = mapped_column(Numeric(12,2), default=0)

    invoice = relationship("Invoice", back_populates="items")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)   
