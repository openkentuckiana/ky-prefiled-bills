import json
import os
import re
import urllib

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
CLIENT_SECRET = json.loads(os.getenv("CLIENT_SECRET"))
PREFILED_BILLS_PAGE = os.getenv(
    "PREFILED_BILLS_PAGE", "https://apps.legislature.ky.gov/record/20rs/prefiled/prefiled_bills.html"
)
PAGES = {
    'Prefiled Bills': PREFILED_BILLS_PAGE,
}
BILL_REQUEST_URL_RE = r"(BR\d+\.html)"

SHEET_HEADERS = ["Bill Number", "Bill Title", "Bill Sponsors", "Last Action"]
MAX_COLUMN = chr(97 + len(SHEET_HEADERS)-1).upper()

def run():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(CLIENT_SECRET, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    worksheet_titles = [s.title for s in spreadsheet.worksheets()]

    for sheet_name, page_url in PAGES.items():
        rows = []
        page = urllib.request.urlopen(page_url)
        soup = BeautifulSoup(page, "html.parser")

        _create_sheet(spreadsheet, sheet_name, worksheet_titles)

        bill_request_urls = re.findall(BILL_REQUEST_URL_RE, str(soup))
        bill_request_urls.sort(key=lambda u: int(re.sub(".html", "", re.sub("BR", "", u))))

        added_bills = spreadsheet.worksheet(sheet_name).col_values(1)
        start_at_row = len(added_bills) + 1

        for url in bill_request_urls:
            bill_number = url.replace(".html", "")
            if bill_number in added_bills:
                print(f"Skipping bill {bill_number}, which already exists")
                continue

            values = [None for i in range(len(SHEET_HEADERS))]

            page = urllib.request.urlopen(PREFILED_BILLS_PAGE.replace("prefiled_bills.html", url))
            soup = BeautifulSoup(page, "html.parser")

            tables = soup.find_all("div", {"class": "bill-table"})
            if len(tables) > 0:
                bill_detail_rows = tables[0].find("tbody").find_all("tr")
                for row in bill_detail_rows:
                    header = row.find_all("th")[0].text.strip()
                    values[0] = bill_number
                    if f"Bill {header}" in SHEET_HEADERS:
                        values[SHEET_HEADERS.index(f"Bill {header}")] = re.sub(r"\s+", " ", row.find_all("td")[0].text.strip())
                if len(tables) > 1:
                    bill_action_rows = tables[1].find("tbody").find_all("tr")
                    if bill_action_rows:
                        last_row = bill_action_rows[-1]
                        values[SHEET_HEADERS.index("Last Action")] = last_row.find_all("td")[0].text.strip()
                    else:
                        print(f"Didn't find any actions for {bill_number}")
                else:
                    print(f"Skipping actions for {bill_number}")
                print(f"Adding {values}")
                rows.append(values)
            else:
                print(f"Could not find bill table for {bill_number}")

        _add_bills(rows, start_at_row, sheet_name, spreadsheet)


def _add_bills(rows, start_at_row, sheet_name, spreadsheet):
    if not rows:
        return
    max_row = len(rows) + start_at_row - 1
    num_columns = len(SHEET_HEADERS)
    worksheet = spreadsheet.worksheet(sheet_name)
    cell_list = worksheet.range(f"B{start_at_row}:{MAX_COLUMN}{max_row}")

    row_num = 0
    column_number = 1
    for cell in cell_list:
        if column_number == 1:
            worksheet.update_cell(
                cell.row, 1,
                f'=HYPERLINK("https://apps.legislature.ky.gov/recorddocuments/bill/20RS/{rows[row_num][0]}/orig_bill.pdf", "{rows[row_num][0]}")',
            )
        cell.value = rows[row_num][column_number]
        if column_number == (num_columns - 1):
            row_num += 1
            column_number = 1
        else:
            column_number += 1

    worksheet.update_cells(cell_list)


def _create_sheet(spreadsheet, sheet_name, worksheet_titles):
    if sheet_name not in worksheet_titles:
        spreadsheet.add_worksheet(sheet_name, 500, 8)

    summary_sheet = spreadsheet.worksheet(sheet_name)

    if not summary_sheet.row_values(1):
        cell_list = summary_sheet.range(f"A1:{MAX_COLUMN}1")

        i = 0
        for cell in cell_list:
            cell.value = SHEET_HEADERS[i]
            i += 1

        summary_sheet.update_cells(cell_list)


if __name__ == "__main__":
    print("Running...")
    run()
    print("Done!")
