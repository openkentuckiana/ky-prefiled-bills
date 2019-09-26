import json
import os
import re
import urllib

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Prefiled Bills")
CLIENT_SECRET = json.loads(os.getenv("CLIENT_SECRET"))
PREFILED_BILLS_PAGE = os.getenv(
    "PREFILED_BILLS_PAGE", "https://apps.legislature.ky.gov/record/20rs/prefiled/prefiled_bills.html"
)
BILL_REQUEST_URL_RE = r"(BR\d+\.html)"
SUMMARY_SHEET_NAME = "Summary"
SUMMARY_SHEET_HEADERS = ["Bill Request", "KEJC Category & Summarizer", "KEJC Summary", "Status"]

BILL_ROWS = [
    "Link to Bill Text",
    "KEJC Category & Summarizer",
    "KEJC Summary",
    "Title",
    "Sponsors",
    "Summary of Original Version",
    "Index Headings",
]


def run():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(CLIENT_SECRET, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet_titles = [s.title for s in spreadsheet.worksheets()]

    _create_summary_sheet(spreadsheet, worksheet_titles)

    page = urllib.request.urlopen(PREFILED_BILLS_PAGE)
    soup = BeautifulSoup(page, "html.parser")

    bill_request_urls = re.findall(BILL_REQUEST_URL_RE, str(soup))
    bill_request_urls.sort()

    for url in bill_request_urls:
        bill_number = url.replace(".html", "")
        if bill_number in worksheet_titles:
            print(f"Skipping bill {bill_number}, which already exists")
            continue

        values = [None for i in range(len(BILL_ROWS))]

        page = urllib.request.urlopen(PREFILED_BILLS_PAGE.replace("prefiled_bills.html", url))
        soup = BeautifulSoup(page, "html.parser")
        table_body = soup.find("tbody")
        rows = table_body.find_all("tr")
        for row in rows:
            header = row.find_all("th")[0].text.strip()
            if header in BILL_ROWS:
                values[BILL_ROWS.index(header)] = row.find_all("td")[0].text.strip()
        _add_bill(bill_number, values, spreadsheet)


def _add_bill(bill_number, values, spreadsheet):
    print(f"Adding bill number {bill_number}")
    summary_sheet = spreadsheet.worksheet("Summary")
    bill_sheet = spreadsheet.add_worksheet(bill_number, 5, 2)

    cell_list = bill_sheet.range("A1:A7")
    i = 0
    for cell in cell_list:
        cell.value = BILL_ROWS[i]
        i += 1
    bill_sheet.update_cells(cell_list)

    cell_list = bill_sheet.range("B1:B7")
    i = 0
    for cell in cell_list:
        cell.value = values[i]
        i += 1
    bill_sheet.update_cells(cell_list)
    bill_sheet.update_acell(
        "B1",
        f'=HYPERLINK("https://apps.legislature.ky.gov/recorddocuments/bill/20RS/{bill_number}/orig_bill.pdf", "Original Bill PDF")',
    )

    ss_last_row = len(summary_sheet.col_values(1)) + 1
    summary_sheet.update_cell(ss_last_row, 1, bill_number)


def _create_summary_sheet(spreadsheet, worksheet_titles):
    if SUMMARY_SHEET_NAME not in worksheet_titles:
        spreadsheet.add_worksheet(SUMMARY_SHEET_NAME, 500, 4)

    summary_sheet = spreadsheet.worksheet(SUMMARY_SHEET_NAME)

    if not summary_sheet.row_values(1):
        cell_list = summary_sheet.range("A1:D1")

        i = 0
        for cell in cell_list:
            cell.value = SUMMARY_SHEET_HEADERS[i]
            i += 1

        summary_sheet.update_cells(cell_list)


if __name__ == "__main__":
    print("Running...")
    run()
    print("Done!")
