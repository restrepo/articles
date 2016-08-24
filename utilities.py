#/usr/bin/env python
from bs4 import BeautifulSoup
import pandas as pd
def html_to_DataFrame(html_page_with_table,attrs={},headings=[]):
    '''
    Extract the table of a web page and convert to a pandas DataFrame
    '''

    soup = BeautifulSoup(html_page_with_table,"lxml")
    table = soup.find("table",attrs)

    # The first tr contains the field names.
    if table:
        if not headings:
            headings = [th.get_text().strip() for th in table.find("tr").find_all("td")]

        datasets = []
        for row in table.find_all("tr")[1:]:
            dataset = [td.get_text() for td in row.find_all("td") if td.get_text().strip()]
            datasets.append(dataset)
        
        if headings:  
            return pd.DataFrame(datasets,columns=headings)
    else:
        return pd.DataFrame()