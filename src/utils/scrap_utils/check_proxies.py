import random
import requests


async def load_proxies():
    valid_proxies = []
    print("Loading proxies...")
    with open("proxies_list.txt", "r") as f:
        proxies = f.read().splitlines()
        for proxy in proxies:
            print(f"Checking proxy {proxy}")
            if await check_proxy(proxy):
                print(f"Proxy {proxy} is valid")
                valid_proxies.append(proxy)
                break
    return valid_proxies


async def check_proxy(proxy):
    try:
        response = await requests.get(
            "https://ipinfo.io/json",
            proxies={"http": proxy, "https": proxy},
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


async def get_random_proxy(valid_proxies):
    print("Getting random proxy...")
    if valid_proxies:
        return await random.choice(valid_proxies)
    return None
