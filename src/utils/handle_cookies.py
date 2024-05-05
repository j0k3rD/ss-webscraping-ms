import pickle

async def get_cookies(page):
    cookies = await page.context.cookies()
    pickle.dump(cookies, open("cookies.pkl", "wb"))        

async def set_cookie(page):
    cookies = pickle.load(open("cookies.pkl", "rb"))

    for cookie in cookies:
        await page.context.add_cookies([cookie])