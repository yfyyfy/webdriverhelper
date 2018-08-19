import json
from selenium import webdriver
from time import sleep

from logging import basicConfig, getLogger, INFO as LEVEL
basicConfig(format='[%(levelname)s] %(name)s %(message)s', level=LEVEL)
logger = getLogger(__name__)

TOSEND   = 'requestWillBeSent'
RECEIVED = 'responseReceived'
FINISHED = 'loadingFinished'

def write_to_file(driver, logType, filename):
    with open(filename, mode='w') as f:
        ret = driver.execute('getLog', {'type': logType})
        f.write(json.dumps(ret, indent=2, sort_keys=True))

# https://codereview.stackexchange.com/questions/156144/get-value-from-dictionary-given-a-list-of-nested-keys
def nested_get(input_dict, nested_key):
    internal_dict_value = input_dict
    for k in nested_key:
        internal_dict_value = internal_dict_value.get(k, None)
        if internal_dict_value is None:
            return None
    return internal_dict_value

def get_params(logJson, method, paramKeys):
    values = logJson['value']
    messages = [json.loads(value['message']) for value in values]
    messages = [message['message'] for message in messages]
    messages = [message for message in messages if message['method'] == method]
    params = [message['params'] for message in messages]
    return [{key:nested_get(param, paramKey) for key, paramKey in paramKeys.items()} for param in params]

def log_progress(request_ids):
    logger.info('#toSend, #received, #finished: %s, %s, %s', len(request_ids[TOSEND]) ,len(request_ids[RECEIVED]) ,len(request_ids[FINISHED]))
    requestWillBeSentId_responseReceivedId = request_ids[TOSEND] - request_ids[RECEIVED]
    if requestWillBeSentId_responseReceivedId:
        logger.info('Requested but not received: %s', requestWillBeSentId_responseReceivedId)
    responseReceivedId_loadingFinishedId = request_ids[RECEIVED]  - request_ids[FINISHED]
    if responseReceivedId_loadingFinishedId:
        logger.info('Received but not finished: %s',  responseReceivedId_loadingFinishedId)
    responseReceivedId_requestWillBeSentId = request_ids[RECEIVED] - request_ids[TOSEND]
    if responseReceivedId_requestWillBeSentId:
        logger.warn('Received but not requested: %s', responseReceivedId_requestWillBeSentId)
    loadingFinishedId_responseReceivedId = request_ids[FINISHED]  - request_ids[RECEIVED]
    if loadingFinishedId_responseReceivedId:
        logger.warn('Finished but not received: %s', loadingFinishedId_responseReceivedId)

def wait_async_loading(driver, delta=5, maxTry=25, break_threshold=2):
    id2url = dict()
    succeeded = False

    nochange_count = 0

    request_ids = {TOSEND: set(), RECEIVED: set(), FINISHED: set()}
    for count in range(0, maxTry):
        if nochange_count >= break_threshold - 1:
            succeeded = True
            break

        sleep(delta)

        logJson = driver.execute('getLog', {'type': 'performance'})
        logs = {TOSEND:   get_params(logJson, 'Network.requestWillBeSent', {'id': ['requestId'], 'url': ['request', 'url']}),
                RECEIVED: get_params(logJson, 'Network.responseReceived',  {'id': ['requestId'], 'url': ['response', 'url']}),
                FINISHED: get_params(logJson, 'Network.loadingFinished',   {'id': ['requestId']})}

        for key in [TOSEND, RECEIVED, FINISHED]:
            request_ids[key].update([e['id'] for e in logs[key]])

        log_progress(request_ids)

        for logslogs in logs[TOSEND], logs[RECEIVED]:
            for log in logslogs:
                urls = id2url.get(log['id'])
                if urls is None:
                    urls = []
                    id2url[log['id']] = urls
                if not (log['url'] in urls):
                    urls.append(log['url'])

        if len(logs[TOSEND]) == 0 and len(logs[RECEIVED]) == 0 and len(logs[FINISHED]) == 0 and len(request_ids[TOSEND] - request_ids[FINISHED]) == 0:
            nochange_count = nochange_count + 1
        else:
            nochange_count = 0

    return {'succeeded': succeeded, 'requests': id2url}

def main():
    exe = "../../chromedriver.exe"
    capabilities = {
        'loggingPrefs': {
            'browser':     'ALL',
            'driver':      'ALL',
            'performance': 'ALL'
        }}
    url = 'https://www.google.co.jp/'

    try:
        driver = webdriver.Chrome(executable_path=exe, desired_capabilities=capabilities)
        driver.get(url)
        requests = wait_async_loading(driver)
    finally:
        driver.quit()

    logger.info('Succeeded: %s', requests['succeeded'])
    # logger.info(json.dumps(requests, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
