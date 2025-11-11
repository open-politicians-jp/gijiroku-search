

import codecs
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin
import re

def get_reason_for_submission(page_url):
    try:
        response = requests.get(page_url)
        response.encoding = 'shift_jis'
        soup = BeautifulSoup(response.text, 'html.parser')

        final_page_url = page_url
        final_soup = soup

        link_tag = soup.find('a', href=re.compile(r"(houan|ketsugian)"))
        if link_tag:
            final_page_url = urljoin(page_url, link_tag['href'])
            response = requests.get(final_page_url)
            response.encoding = 'shift_jis'
            final_soup = BeautifulSoup(response.text, 'html.parser')

        reason_header = final_soup.find(lambda tag: tag.name.lower() == 'h3' and '理' in tag.get_text() and '由' in tag.get_text())
        if reason_header:
            next_p = reason_header.find_next_sibling('p')
            if next_p:
                return next_p.get_text(strip=True)

        if 'ketsugian' in final_page_url:
            p_tag = final_soup.find('p', class_='txt03')
            if p_tag:
                return p_tag.get_text(strip=True)

        return "理由が見つかりません"

    except Exception as e:
        return f"理由の取得中にエラー: {e}"

def main():
    html_file_path = '/Users/hironeko/Work/private/new-jp-search/shugiin_bills.html'
    output_file_path = '/Users/hironeko/Work/private/new-jp-search/tmp.md'
    base_url = "https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/"

    try:
        with codecs.open(html_file_path, 'r', 'shift_jis') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file {html_file_path} was not found.")
        return
    except Exception as e:
        print(f"Error reading the file: {e}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    # Corrected the table selection to be more general.
    tables = soup.find_all('table', class_="table")

    with open(output_file_path, 'w', encoding='utf-8') as md_file:
        md_file.write("| 提出回次 | 番号 | 議案件名 | 審議状況 | 経過情報のURL | 本文情報のURL | 提出時法案の理由 |\n")
        md_file.write("|---|---|---|---|---|---|---|\n")

        for table in tables:
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')

                if len(cols) == 6:
                    session, number, name, status_cell, progress_cell, text_cell = cols
                    text_link = text_cell.find('a')
                elif len(cols) == 5:
                    session, number, name, status_cell, progress_cell = cols
                    text_link = None
                else:
                    continue

                submission_session = session.get_text(strip=True)
                bill_number = number.get_text(strip=True)
                bill_name = name.get_text(strip=True)
                status = status_cell.get_text(strip=True)
                progress_link = progress_cell.find('a')

                progress_url = urljoin(base_url, progress_link['href']) if progress_link else "N/A"

                reason = "適用しない"
                text_url = "N/A"
                if text_link:
                    text_url = urljoin(base_url, text_link['href'])
                    reason = get_reason_for_submission(text_url)

                md_file.write(f"| {submission_session} | {bill_number} | {bill_name} | {status} | {progress_url} | {text_url} | {reason} |\n")

    print(f"Markdown table has been written to {output_file_path}")

if __name__ == "__main__":
    main()

