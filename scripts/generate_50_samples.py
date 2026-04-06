#!/usr/bin/env python3
"""Generate 50 varied sample PDFs for testing the ingestion/cleaning pipeline.

This script creates realistic but synthetic real estate documents across:
- Multiple silos (comps, offering_memo, appraisals, leases, financials)
- Different property types (office, retail, industrial, multifamily, mixed-use)
- Varied formatting (dates, currencies, area units)
- Edge cases (low text, tables, repeated headers, noisy content)
"""

from pathlib import Path
import random

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# Property types and their typical characteristics
PROPERTY_TYPES = [
    "Office Tower",
    "Retail Center",
    "Industrial Warehouse",
    "Multifamily Complex",
    "Mixed-Use Development",
    "Medical Office Building",
    "Self-Storage Facility",
    "Data Center",
    "Hotel",
    "Senior Living Facility",
]

LOCATIONS = [
    "Downtown Chicago",
    "Suburban Atlanta",
    "Miami Beach",
    "San Francisco CBD",
    "Austin Tech Corridor",
    "Denver LoDo",
    "Phoenix Midtown",
    "Seattle Waterfront",
    "Boston Back Bay",
    "Nashville Downtown",
    "Portland Pearl District",
    "Dallas Uptown",
    "Los Angeles DTLA",
    "New York Midtown",
    "Charlotte South End",
]

# Varied date formats to test normalization
DATE_FORMATS = [
    lambda m, d, y: f"{m}/{d}/{y}",           # 3/15/2025
    lambda m, d, y: f"{m:02d}/{d:02d}/{y}",   # 03/15/2025
    lambda m, d, y: f"{y}-{m:02d}-{d:02d}",   # 2025-03-15
    lambda m, d, y: f"{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]} {d}, {y}",  # Mar 15, 2025
]

# Varied currency formats to test normalization
CURRENCY_FORMATS = [
    lambda v: f"$ {v:,}",           # $ 1,250,000
    lambda v: f"${v:,}",            # $1,250,000
    lambda v: f"$ {v:,.2f}",        # $ 1,250,000.00
    lambda v: f"{v/1000000:.1f}M",  # 1.3M
    lambda v: f"${v/1000000:.2f}M", # $1.25M
]

# Varied area unit formats to test normalization
AREA_FORMATS = [
    lambda sf: f"{sf:,} SF",
    lambda sf: f"{sf:,} sq ft",
    lambda sf: f"{sf:,} sqft",
    lambda sf: f"{sf:,} sq. ft.",
    lambda sf: f"{sf:,} square feet",
]

# Headers that repeat across pages (to test header removal)
REPEATED_HEADERS = [
    "CONFIDENTIAL - DO NOT DISTRIBUTE",
    "PROPRIETARY INFORMATION",
    "DRAFT - FOR DISCUSSION ONLY",
    "STRICTLY CONFIDENTIAL",
    "INTERNAL USE ONLY",
]

REPEATED_FOOTERS = [
    "This document contains confidential information.",
    "All rights reserved.",
    "Prepared by ABC Valuation Services",
    "For authorized recipients only.",
]


def random_date():
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    year = random.randint(2023, 2026)
    formatter = random.choice(DATE_FORMATS)
    return formatter(month, day, year)


def random_currency(min_val=500000, max_val=50000000):
    value = random.randint(min_val // 1000, max_val // 1000) * 1000
    formatter = random.choice(CURRENCY_FORMATS)
    return formatter(value), value


def random_area(min_sf=5000, max_sf=500000):
    sf = random.randint(min_sf // 100, max_sf // 100) * 100
    formatter = random.choice(AREA_FORMATS)
    return formatter(sf), sf


def random_cap_rate():
    rate = random.uniform(4.0, 10.0)
    formats = [
        f"Cap Rate: {rate:.1f}%",
        f"cap rate is {rate:.2f}%",
        f"Cap Rate = {rate:.1f}%",
        f"Capitalization Rate of {rate:.2f}%",
    ]
    return random.choice(formats), rate


def generate_comp_report(idx: int) -> list[str]:
    """Generate a comparable sales report (1-3 pages)."""
    prop_type = random.choice(PROPERTY_TYPES)
    location = random.choice(LOCATIONS)
    header = random.choice(REPEATED_HEADERS)
    footer = random.choice(REPEATED_FOOTERS)

    sale_price, price_val = random_currency(1000000, 30000000)
    area, sf_val = random_area(10000, 200000)
    price_psf = price_val / sf_val
    cap_rate_str, cap_rate = random_cap_rate()
    noi, noi_val = random_currency(100000, 3000000)

    pages = []

    # Page 1: Summary
    page1 = f"""{header}

COMPARABLE SALE REPORT #{idx}

Property: {prop_type}
Location: {location}
Sale Date: {random_date()}

TRANSACTION SUMMARY

Sale Price: {sale_price}
Building Size: {area}
Price per SF: ${price_psf:,.2f}
{cap_rate_str}
NOI at Sale: {noi}

Page 1 of 2

{footer}"""
    pages.append(page1)

    # Page 2: Details
    page2 = f"""{header}

PROPERTY DETAILS

Year Built: {random.randint(1970, 2020)}
Occupancy at Sale: {random.randint(75, 100)}%
Parking Ratio: {random.uniform(2.0, 5.0):.1f} per 1,000 SF
Zoning: {random.choice(['C-2', 'M-1', 'B-3', 'PUD', 'MU-1'])}

BUYER/SELLER INFORMATION

Buyer: {random.choice(['Private Investor', 'REIT', 'Pension Fund', 'Family Office', 'Institutional'])}
Seller: {random.choice(['Developer', 'Private Owner', 'Bank (REO)', 'Estate Sale', 'Corporate'])}

Transaction recorded on {random_date()}

Page 2 of 2

{footer}"""
    pages.append(page2)

    return pages


def generate_offering_memo(idx: int) -> list[str]:
    """Generate an offering memorandum (2-4 pages)."""
    prop_type = random.choice(PROPERTY_TYPES)
    location = random.choice(LOCATIONS)
    header = random.choice(REPEATED_HEADERS)

    asking_price, price_val = random_currency(5000000, 50000000)
    area, sf_val = random_area(20000, 300000)
    noi, noi_val = random_currency(300000, 5000000)
    cap_rate_str, cap_rate = random_cap_rate()

    pages = []

    # Page 1: Executive Summary
    page1 = f"""{header}

OFFERING MEMORANDUM
{prop_type} - {location}

EXECUTIVE SUMMARY

We are pleased to present this exceptional investment opportunity.

Asking Price: {asking_price}
{cap_rate_str}
Net Operating Income: {noi}
Rentable Area: {area}

Key Investment Highlights:
- Prime location in {location}
- Stabilized occupancy of {random.randint(85, 98)}%
- Recent capital improvements of {random_currency(100000, 2000000)[0]}
- Strong tenant roster with weighted avg lease term of {random.uniform(3, 8):.1f} years

Page 1 of 3

{header}"""
    pages.append(page1)

    # Page 2: Financial Overview
    rent_psf = random.uniform(15, 45)
    page2 = f"""{header}

FINANCIAL OVERVIEW

INCOME                          ANNUAL
Base Rent                       {random_currency(400000, 4000000)[0]}
CAM Reimbursements             {random_currency(50000, 500000)[0]}
Other Income                    {random_currency(10000, 100000)[0]}
                               ---------------
Effective Gross Income          {random_currency(500000, 5000000)[0]}

EXPENSES
Property Taxes                  {random_currency(50000, 400000)[0]}
Insurance                       {random_currency(20000, 100000)[0]}
Utilities                       {random_currency(30000, 200000)[0]}
Management ({random.uniform(3, 5):.1f}%)              {random_currency(20000, 150000)[0]}
Repairs & Maintenance           {random_currency(25000, 150000)[0]}
                               ---------------
Total Expenses                  {random_currency(150000, 1000000)[0]}

NET OPERATING INCOME            {noi}

Average Rent: ${rent_psf:.2f} per sqft

Page 2 of 3"""
    pages.append(page2)

    # Page 3: Market Overview
    page3 = f"""{header}

MARKET OVERVIEW

{location} continues to demonstrate strong fundamentals.

Market Statistics:
- Vacancy Rate: {random.uniform(5, 15):.1f}%
- Avg Asking Rent: ${random.uniform(18, 50):.2f}/SF
- YTD Absorption: {random.randint(-50000, 200000):,} SF
- Under Construction: {random.randint(0, 500000):,} SF

Comparable recent sales in the submarket:
- {random.choice(PROPERTY_TYPES)} sold {random_date()} at {random_currency(3000000, 20000000)[0]}
- {random.choice(PROPERTY_TYPES)} sold {random_date()} at {random_currency(3000000, 20000000)[0]}

Report prepared on {random_date()}

Page 3 of 3

{random.choice(REPEATED_FOOTERS)}"""
    pages.append(page3)

    return pages


def generate_appraisal(idx: int) -> list[str]:
    """Generate an appraisal report (2-3 pages)."""
    prop_type = random.choice(PROPERTY_TYPES)
    location = random.choice(LOCATIONS)
    header = "APPRAISAL REPORT - CONFIDENTIAL"

    appraised_value, value = random_currency(2000000, 40000000)
    area, sf_val = random_area(15000, 250000)

    pages = []

    # Page 1
    page1 = f"""{header}

SUMMARY APPRAISAL REPORT

Property Address: 123 Main Street, {location}
Property Type: {prop_type}
Effective Date of Appraisal: {random_date()}
Date of Report: {random_date()}

OPINION OF VALUE

Based on our analysis, the market value of the subject property is:

    {appraised_value}

(Say: {random.choice(['Two', 'Three', 'Five', 'Ten', 'Fifteen', 'Twenty'])} Million Dollars)

Property Size: {area}
Value per SF: ${value/sf_val:,.2f}

Page 1 of 2"""
    pages.append(page1)

    # Page 2: Approaches
    cap_rate_str, cap_rate = random_cap_rate()
    page2 = f"""{header}

VALUATION APPROACHES

INCOME APPROACH
Potential Gross Income:     {random_currency(400000, 4000000)[0]}
Less: Vacancy ({random.uniform(3, 8):.1f}%)       ({random_currency(20000, 200000)[0]})
Effective Gross Income:     {random_currency(350000, 3500000)[0]}
Less: Operating Expenses:   ({random_currency(100000, 1000000)[0]})
Net Operating Income:       {random_currency(200000, 2500000)[0]}
{cap_rate_str}
Value by Income Approach:   {appraised_value}

SALES COMPARISON APPROACH
Comparable 1: {random_currency(1500000, 35000000)[0]} ({random_date()})
Comparable 2: {random_currency(1500000, 35000000)[0]} ({random_date()})
Comparable 3: {random_currency(1500000, 35000000)[0]} ({random_date()})
Adjusted Value Indication:  {random_currency(int(value*0.95), int(value*1.05))[0]}

RECONCILIATION
Final Opinion of Value:     {appraised_value}

Appraiser: John Smith, MAI
License #: {random.randint(10000, 99999)}

Page 2 of 2"""
    pages.append(page2)

    return pages


def generate_lease_abstract(idx: int) -> list[str]:
    """Generate a lease abstract (1-2 pages)."""
    prop_type = random.choice(PROPERTY_TYPES[:5])
    location = random.choice(LOCATIONS)
    tenant = random.choice([
        "ABC Corporation", "XYZ Holdings LLC", "National Retailer Inc",
        "Tech Startup Co", "Medical Group PA", "Law Offices of Smith",
        "Regional Bank NA", "Insurance Agency LLC", "Consulting Group Inc"
    ])

    area, sf_val = random_area(1000, 50000)
    base_rent = random.uniform(15, 50)

    pages = []

    page1 = f"""LEASE ABSTRACT

PROPERTY: {prop_type} at {location}
TENANT: {tenant}
LEASE DATE: {random_date()}

PREMISES
Suite: {random.randint(100, 900)}
Rentable Area: {area}
Pro Rata Share: {random.uniform(5, 30):.2f}%

TERM
Commencement: {random_date()}
Expiration: {random_date()}
Initial Term: {random.choice([3, 5, 7, 10])} years

RENT
Base Rent: ${base_rent:.2f} per sqft annually
Monthly Base Rent: {random_currency(int(sf_val * base_rent / 12), int(sf_val * base_rent / 12) + 1000)[0]}
Annual Escalation: {random.uniform(2, 4):.1f}%

ADDITIONAL RENT
CAM: ${random.uniform(5, 15):.2f}/SF
Taxes: ${random.uniform(3, 10):.2f}/SF
Insurance: ${random.uniform(0.5, 2):.2f}/SF

OPTIONS
Renewal: {random.randint(1, 3)} x {random.choice([3, 5])} year options
Expansion: {random.choice(['Yes - ROFO on adjacent', 'No', 'Yes - up to 5,000 SF'])}

Abstracted on {random_date()}

Page 1 of 1"""
    pages.append(page1)

    return pages


def generate_financial_statement(idx: int) -> list[str]:
    """Generate a financial/NOI statement (1-2 pages)."""
    prop_type = random.choice(PROPERTY_TYPES)
    location = random.choice(LOCATIONS)

    # Generate realistic financials
    gross_rent = random.randint(500, 5000) * 1000
    vacancy = gross_rent * random.uniform(0.03, 0.10)
    egi = gross_rent - vacancy
    expenses = egi * random.uniform(0.30, 0.45)
    noi = egi - expenses

    pages = []

    page1 = f"""OPERATING STATEMENT
{prop_type} - {location}
For the Period Ending {random_date()}

                                    ACTUAL          BUDGET          VARIANCE
REVENUE
Gross Potential Rent              {random_currency(int(gross_rent), int(gross_rent)+1)[0]}    {random_currency(int(gross_rent*1.02), int(gross_rent*1.02)+1)[0]}
Less: Vacancy & Credit Loss      ({random_currency(int(vacancy), int(vacancy)+1)[0]})   ({random_currency(int(vacancy*0.95), int(vacancy*0.95)+1)[0]})
                                  ---------------  ---------------
Effective Gross Income            {random_currency(int(egi), int(egi)+1)[0]}    {random_currency(int(egi*1.01), int(egi*1.01)+1)[0]}

OPERATING EXPENSES
Property Taxes                    {random_currency(int(expenses*0.25), int(expenses*0.25)+1)[0]}
Insurance                         {random_currency(int(expenses*0.08), int(expenses*0.08)+1)[0]}
Utilities                         {random_currency(int(expenses*0.15), int(expenses*0.15)+1)[0]}
Repairs & Maintenance            {random_currency(int(expenses*0.20), int(expenses*0.20)+1)[0]}
Management Fee                    {random_currency(int(expenses*0.12), int(expenses*0.12)+1)[0]}
Administrative                    {random_currency(int(expenses*0.10), int(expenses*0.10)+1)[0]}
Other                            {random_currency(int(expenses*0.10), int(expenses*0.10)+1)[0]}
                                  ---------------
Total Operating Expenses          {random_currency(int(expenses), int(expenses)+1)[0]}

NET OPERATING INCOME              {random_currency(int(noi), int(noi)+1)[0]}

Occupancy Rate: {random.randint(85, 98)}%
Expense Ratio: {expenses/egi*100:.1f}%

Prepared on {random_date()}

Page 1 of 1"""
    pages.append(page1)

    return pages


def generate_edge_case_low_text(idx: int) -> list[str]:
    """Generate a document with very little text (edge case)."""
    return [
        "Cover Page",
        f"Page {idx}",
        "END",
    ]


def generate_edge_case_table_heavy(idx: int) -> list[str]:
    """Generate a table-heavy document."""
    header = "RENT ROLL SUMMARY"

    rows = []
    rows.append(f"{header}\n\nAs of {random_date()}\n")
    rows.append("Suite | Tenant | SF | Rent/SF | Annual Rent | Lease End")
    rows.append("-" * 70)

    for i in range(random.randint(5, 15)):
        suite = f"{random.randint(1,9)}0{random.randint(0,9)}"
        tenant = random.choice(["Acme Co", "Beta Inc", "Gamma LLC", "Delta Corp", "Vacant"])
        sf = random.randint(1, 50) * 100
        rent_sf = random.uniform(15, 45)
        annual = sf * rent_sf
        lease_end = random_date() if tenant != "Vacant" else "N/A"
        rows.append(f"{suite} | {tenant} | {sf:,} | ${rent_sf:.2f} | ${annual:,.0f} | {lease_end}")

    rows.append("-" * 70)
    rows.append(f"Total: {random.randint(10000, 100000):,} SF")

    return ["\n".join(rows)]


def write_pdf(path: Path, pages: list[str]) -> None:
    """Write pages to a PDF file."""
    pdf = canvas.Canvas(str(path), pagesize=letter)

    for page_text in pages:
        y = 750
        for line in page_text.split("\n"):
            if y < 50:
                pdf.showPage()
                y = 750
            pdf.drawString(50, y, line[:100])  # Truncate long lines
            y -= 14
        pdf.showPage()

    pdf.save()


def main():
    output_dir = Path(__file__).parent.parent / "sample_data_50"

    # Create silo directories
    silos = {
        "comps": output_dir / "comps",
        "offering_memo": output_dir / "offering_memo",
        "appraisals": output_dir / "appraisals",
        "leases": output_dir / "leases",
        "financials": output_dir / "financials",
    }

    for silo_dir in silos.values():
        silo_dir.mkdir(parents=True, exist_ok=True)

    # Document generators with weights
    generators = [
        (generate_comp_report, silos["comps"], "comp", 12),
        (generate_offering_memo, silos["offering_memo"], "memo", 10),
        (generate_appraisal, silos["appraisals"], "appraisal", 10),
        (generate_lease_abstract, silos["leases"], "lease", 8),
        (generate_financial_statement, silos["financials"], "financial", 6),
        (generate_edge_case_low_text, silos["comps"], "lowtext", 2),
        (generate_edge_case_table_heavy, silos["financials"], "rentroll", 2),
    ]

    # Generate 50 documents
    doc_idx = 0
    total_docs = 50

    # Distribute documents according to weights
    doc_queue = []
    for gen_func, silo_dir, prefix, weight in generators:
        for _ in range(weight):
            doc_queue.append((gen_func, silo_dir, prefix))

    random.shuffle(doc_queue)

    for i in range(total_docs):
        gen_func, silo_dir, prefix = doc_queue[i % len(doc_queue)]
        doc_idx += 1

        pages = gen_func(doc_idx)
        filename = f"{prefix}_{doc_idx:03d}.pdf"
        filepath = silo_dir / filename

        write_pdf(filepath, pages)
        print(f"Generated: {filepath.relative_to(output_dir.parent)}")

    print(f"\nGenerated {total_docs} PDFs in {output_dir}")
    print("\nSilo distribution:")
    for name, silo_dir in silos.items():
        count = len(list(silo_dir.glob("*.pdf")))
        print(f"  {name}: {count} files")


if __name__ == "__main__":
    main()