import httpx
import asyncio
from datetime import datetime
from pprint import pformat
import os
import time

log_requests_debug = True


def target_predicate(resp):
    return \
        resp.json()['data']['product']['fulfillment']['store_options'][0].get('in_store_only')['availability_status'] == 'IN_STOCK' or \
        resp.json()['data']['product']['fulfillment']['store_options'][0].get('order_pickup')['availability_status'] == 'IN_STOCK' or \
        resp.json()['data']['product']['fulfillment']['store_options'][0].get('ship_to_store')['availability_status'] == 'IN_STOCK'

def bestbuy_predicate(resp):
    return 'Add to Cart' in resp.text


playstations = [
    # {
    #     'name': 'Target, Hadley, PS5 Controller',
    #     'url': 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114477&store_id=1839&store_positions_store_id=1839&has_store_positions_store_id=true&zip=01075&state=MA&latitude=42.24842&longitude=-72.60757&scheduled_delivery_store_id=1232&pricing_store_id=1839',
    #     'predicate': target_predicate
    # },
    {
        'name': 'Target, Hadley, PS5 Disc Edition',
        'url': 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114596&store_id=1839&store_positions_store_id=1839&has_store_positions_store_id=true&zip=01075&state=MA&latitude=42.24842&longitude=-72.60757&scheduled_delivery_store_id=1232&pricing_store_id=1839',
        'predicate': target_predicate
    },
    {
        'name': 'Target, Hadley, PS5 Digital Edition',
        'url': 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114595&store_id=1839&store_positions_store_id=1839&has_store_positions_store_id=true&zip=01075&state=MA&latitude=42.24842&longitude=-72.60757&scheduled_delivery_store_id=1232&pricing_store_id=1839',
        'predicate': target_predicate
    },
    {
        'name': 'Target, Holyoke, PS5 Disc Edition',
        'url': 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114596&store_id=1232&store_positions_store_id=1232&has_store_positions_store_id=true&zip=01075&state=MA&latitude=42.24842&longitude=-72.60757&scheduled_delivery_store_id=1232&pricing_store_id=1232',
        'predicate': target_predicate
    },
    {
        'name': 'Target, Holyoke, PS5 Digital Edition',
        'url': 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114595&store_id=1232&store_positions_store_id=1232&has_store_positions_store_id=true&zip=01075&state=MA&latitude=42.24842&longitude=-72.60757&scheduled_delivery_store_id=1232&pricing_store_id=1232',
        'predicate': target_predicate
    },
    {
        'name': 'BestBuy, Holyoke, PS5 Disc Edition',
        'url': 'https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p?skuId=6426149',
        'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'Accept': '*/*'},
        'predicate': bestbuy_predicate
    },
    {
        'name': 'BestBuy, Holyoke, PS5 Digital Edition',
        'url': 'https://www.bestbuy.com/site/sony-playstation-5-digital-edition-console/6430161.p?skuId=6430161',
        'headers': {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'Accept': '*/*'},
        'predicate': bestbuy_predicate
    },
    {
        'name': 'Amazon, PS5 Disc Edition',
        'url': 'https://www.amazon.com/PlayStation-5-Console/dp/B08FC5L3RG',
        'headers': {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'Accept': '*/*'},
        'predicate': lambda resp: 'Add to Cart' in resp.text
    },
    {
        'name': 'Walmart, PS5 Disc Edition',
        'url': 'https://www.walmart.com/ip/PlayStation-5-Console/363472942',
        'headers': {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'Accept': '*/*'},
        'predicate': lambda resp: 'Add to cart' in resp.text
    },
    {
        'name': 'Walmart, PS5 Digital Edition',
        'url': 'https://www.walmart.com/ip/Sony-PlayStation-5-Digital-Edition/493824815',
        'headers': {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'Accept': '*/*'},
        'predicate': lambda resp: 'Add to cart' in resp.text
    },
    
]

start_time = datetime.now()
time_format = "%Y%M%d_%H%M%S"

async def request(ps5):
    ps5['req_time'] = datetime.now().isoformat()
    headers = ps5.get('headers', {})
    try:
        async with httpx.AsyncClient(http2=True) as client:
            resp = await client.get(ps5['url'], headers=headers, timeout=6)
            ps5['resp'] = {}
            ps5['resp']['status_code'] = resp.status_code
            ps5['resp']['body'] = resp.text
            if resp.status_code == 200:
                ps5['in_stock'] = ps5['predicate'](resp)
    except Exception as e:
        ps5['exception'] = str(e)


async def make_requests(playstations):
    start = time.monotonic()
    requests = []
    for ps5 in playstations:
        task = asyncio.create_task(request(ps5))
        # print(task)
        requests.append(task)

    await asyncio.gather(*requests)
    end = time.monotonic()
    elapsed = end - start
    print(f"All requests done. Took {elapsed}")

asyncio.run(make_requests(playstations))

for ps5 in playstations:
    if ps5.get('exception'):
        print(f"{ps5['name']} EXCEPTION: {ps5['exception']}") 
    else:
        if ps5['resp']['status_code'] == 200:
            print(f"{ps5['name']}: {'IN STOCK' if ps5['in_stock'] else 'OUT OF STOCK'}")
            if ps5['in_stock']:
                while True:
                    os.system(f'say -v Samantha ALERT! PLAYSTATION AVAILABLE {ps5["name"]}')
        else:
            print(f"{ps5['name']} ERROR: {ps5['resp']['status_code']}")

with open(f'log/ps5_check.{start_time.strftime(time_format)}.log', 'ta') as log:
    log.write(pformat(playstations, indent=2, sort_dicts=False))
    log.write('\n')
