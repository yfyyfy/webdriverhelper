from pathlib import Path
from selenium import webdriver

def search_driver_exe(browser):
    driver_exe_dict = {
        'chrome': 'chromedriver.exe',
        'firefox': 'geckodriver.exe',
        'ie': 'IEDriverServer.exe',
        'safari': None,
    }

    driver_name = driver_exe_dict.get(browser)
    if driver_name is None:
        return None

    for path in Path().resolve().parents:
        res = list(path.glob(driver_name))
        if len(res) > 0:
            return str(res[0])
    return None

def get_webdriver(browser, **kwargs):
    driver_function_dict = {
        'chrome': webdriver.Chrome,
        'firefox': webdriver.Firefox,
        'ie': webdriver.Ie,
        'safari': webdriver.Safari,
    }

    driver_function = driver_function_dict.get(browser)
    if driver_function is None:
        return None

    _kwargs = kwargs.copy()
    exe = search_driver_exe(browser)

    if exe is not None:
        _kwargs.update({
            'executable_path': exe
        })

    return driver_function(**_kwargs)
