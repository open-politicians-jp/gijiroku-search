

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def main():
    base_url = "https://www.sangiin.go.jp/japanese/joho1/kousei/gian/217/"
    initial_url = urljoin(base_url, "gian.htm")
    output_file_path = "/Users/hironeko/Work/private/new-jp-search/tmp2.md"

    try:
        # 1. Find the bill detail page
        response = requests.get(initial_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        bill_link = soup.find('a', string=re.compile(r"所得税法等の一部を改正する法律案"))
        if not bill_link:
            print("目的の法案リンクが見つかりませんでした。")
            return

        detail_page_url = urljoin(base_url, bill_link['href'])

        # 2. Find the voting results page link
        response = requests.get(detail_page_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        saiketsu_header = soup.find('th', string=re.compile(r"採決方法"))
        if not saiketsu_header:
            print("「採決方法」のセクションが見つかりませんでした。")
            return

        vote_link_cell = saiketsu_header.find_next_sibling('td')
        vote_link = vote_link_cell.find('a') if vote_link_cell else None
        if not vote_link or not vote_link.has_attr('href'):
            print("投票結果へのリンクが見つかりませんでした。")
            return

        # Let requests handle the redirect automatically
        voting_page_response = requests.get(urljoin(detail_page_url, vote_link['href']))
        voting_page_response.encoding = 'utf-8'
        voting_soup = BeautifulSoup(voting_page_response.text, 'html.parser')

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 「所得税法等の一部を改正する法律案」の投票結果\n\n")

            # --- Party-level results ---
            f.write("## 政党別投票結果\n\n")
            f.write("| 政党 | 賛成 | 反対 |\n")
            f.write("|:---|---:|---:|\n")

            # Corrected table selection for party results
            # Party results are in <h4 class="party"> followed by <dl class="sanpilist"> with <dt class="party"> for counts
            party_sections = voting_soup.find_all('h4', class_='party')
            for party_section in party_sections:
                party_name = party_section.get_text(strip=True)
                sanpilist_dl = party_section.find_next_sibling('dl', class_='sanpilist')
                if sanpilist_dl:
                    dt_tag = sanpilist_dl.find('dt', class_='party')
                    if dt_tag:
                        counts_text = dt_tag.get_text(strip=True)
                        sansei_match = re.search(r'賛成票\s*(\d+)', counts_text)
                        hantai_match = re.search(r'反対票\s*(\d+)', counts_text)
                        sansei = sansei_match.group(1) if sansei_match else "0"
                        hantai = hantai_match.group(1) if hantai_match else "0"
                        f.write(f"| {party_name} | {sansei} | {hantai} |\n")
            f.write("\n")

            # --- Individual voter results ---
            f.write("## 議員別投票結果\n\n")
            f.write("| 氏名 | 投票 |\n")
            f.write("|:---|:---|\n") # Corrected line

            # Corrected table selection for individual voter results
            vote_tables = voting_soup.find_all('ul', class_='flex')
            for ul_tag in vote_tables:
                for li_tag in ul_tag.find_all('li', class_='giin'):
                    name_span = li_tag.find('span', class_='names')
                    pros_span = li_tag.find('span', class_='pros')
                    cons_span = li_tag.find('span', class_='cons')
                    novote_span = li_tag.find('span', class_='novote')

                    name = name_span.get_text(strip=True) if name_span else "不明"
                    vote_cast = "不明"
                    if pros_span and pros_span.get_text(strip=True) == "賛成":
                        vote_cast = "賛成"
                    elif cons_span and cons_span.get_text(strip=True) == "反対":
                        vote_cast = "反対"
                    elif novote_span:
                        vote_cast = "投票なし"
                    
                    f.write(f"| {name} | {vote_cast} |\n")

        print(f"投票結果が {output_file_path} に保存されました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()

