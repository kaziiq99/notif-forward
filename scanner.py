import asyncio
import aiohttp
import time

DOMAINS = [
    "cabinet.iq", "moedu.gov.iq", "moh.gov.iq", "ur.gov.iq",
    "cosit.gov.iq", "iraq.gov.iq", "mof.gov.iq", "moi.gov.iq",
    "mod.gov.iq", "mop.gov.iq", "mch.gov.iq", "moc.gov.iq",
    "moj.gov.iq", "mola.gov.iq", "mowr.gov.iq", "mtc.gov.iq",
    "mofa.gov.iq", "moo.gov.iq", "mocul.gov.iq", "centralbank.iq",
    "cbi.iq", "asiasell.com.iq", "korek.net", "zain.iq", "iepn.iq"
]

async def check(session, domain):
    url = f"https://{domain}"
    start = time.time()
    try:
        async with session.get(url, timeout=5, allow_redirects=True) as r:
            ms = int((time.time() - start) * 1000)
            return (domain, r.status, ms)
    except asyncio.TimeoutError:
        return (domain, "TIMEOUT", 0)
    except aiohttp.ClientConnectorError:
        return (domain, "REFUSED", 0)
    except Exception:
        return (domain, "FAIL", 0)

async def main():
    headers = {"User-Agent": "Mozilla/5.0 (Android 13) AppleWebKit/537.36"}
    connector = aiohttp.TCPConnector(limit=10, force_close=True)
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        print(f"[*] فحص {len(DOMAINS)} نطاق...\n")
        tasks = [check(session, d) for d in DOMAINS]
        results = await asyncio.gather(*tasks)

        ok = [r for r in results if isinstance(r[1], int)]
        ok.sort(key=lambda x: x[2])

        print("--- نطاقات فتحت (مرتبة بالأسرع) ---")
        for d, code, ms in ok:
            print(f"[+] {d} -> {code} ({ms}ms)")

        print("\n--- نطاقات فشلت ---")
        for d, code, ms in results:
            if not isinstance(code, int):
                print(f"[-] {d} -> {code}")

if __name__ == "__main__":
    asyncio.run(main())
