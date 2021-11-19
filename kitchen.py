# Lab 1 submission

import queue
import time
from itertools import count
from operator import itemgetter
from flask import Flask, request
import threading
import requests

time_unit = 1
foods_q = queue.PriorityQueue()
stoves_q = queue.Queue()
ovens_q = queue.Queue()
stoves_q.put_nowait(0)
stoves_q.put_nowait(1)
stoves_q.put_nowait(2)
stoves_q.put_nowait(3)
ovens_q.put_nowait(0)
ovens_q.put_nowait(1)
ovens_q.put_nowait(2)
ovens_q.put_nowait(3)
orders = []
restaurant_cooks = [{
    "id": 1,
    "rank": 3,
    "proficiency": 4,
    "name": "Alain Ducasse",
    "catch-phrase": "I have 17 Michelin Stars"
}, {
    "id": 2,
    "rank": 3,
    "proficiency": 3,
    "name": "Pierre Gagnaire",
    "catch-phrase": "I have 14 Michelin Stars"
}, {
    "id": 3,
    "rank": 2,
    "proficiency": 3,
    "name": "Gordon Ramsay",
    "catch-phrase": "I have 7 Michelin Stars"
},  {
    "id": 4,
    "rank": 1,
    "proficiency": 2,
    "name": "Gordon Ramsay JR",
    "catch-phrase": "I am learning"
}]

menu = [{
    "id": 1,
    "name": "pizza",
    "preparation-time": 20,
    "complexity": 2,
    "cooking-apparatus": "oven"
}, {
    "id": 2,
    "name": "salad",
    "preparation-time": 10,
    "complexity": 1,
    "cooking-apparatus": None
}, {
    "id": 4,
    "name": "Scallop Sashimi with Meyer Lemon Confit",
    "preparation-time": 32,
    "complexity": 3,
    "cooking-apparatus": None
}, {
    "id": 5,
    "name": "Island Duck with Mulberry Mustard",
    "preparation-time": 35,
    "complexity": 3,
    "cooking-apparatus": "oven"
}, {
    "id": 6,
    "name": "Waffles",
    "preparation-time": 10,
    "complexity": 1,
    "cooking-apparatus": "stove"
}, {
    "id": 7,
    "name": "Aubergine",
    "preparation-time": 20,
    "complexity": 2,
    "cooking-apparatus": None
}, {
    "id": 8,
    "name": "Lasagna",
    "preparation-time": 30,
    "complexity": 2,
    "cooking-apparatus": "oven"
}, {
    "id": 9,
    "name": "Burger",
    "preparation-time": 15,
    "complexity": 1,
    "cooking-apparatus": "oven"
}, {
    "id": 10,
    "name": "Gyros",
    "preparation-time": 15,
    "complexity": 1,
    "cooking-apparatus": None
}]

counter = count(start=1, step=1)

app = Flask(__name__)

@app.route('/order', methods=['POST'])
def order():
    data = request.get_json()
    print(f'New order sent to kitchen server {data["order_id"]} items : {data["items"]} priority : {data["priority"]}' )
    split_order(data)
    return {'isSuccess': True}


def split_order(input_order):
    priority = (-int(input_order['priority']))

    kitchen_order = {
        'order_id': input_order['order_id'],
        'table_id': input_order['table_id'],
        'waiter_id': input_order['waiter_id'],
        'items': input_order['items'],
        'priority': priority,
        'max_wait': input_order['max_wait'],
        'received_time': time.time(),
        'cooking_details': queue.Queue(),
        'prepared_items': 0,
        'time_start': input_order['time_start'],
    }
    orders.append(kitchen_order)
    #split each order in a items queue available for cooks
    for idx in input_order['items']:
        food_item = next((f for i, f in enumerate(menu) if f['id'] == idx), None)
        if food_item is not None:
            foods_q.put_nowait((priority, next(counter),{
                'food_id': food_item['id'],
                'order_id': input_order['order_id'],
                'priority': int(input_order['priority'])
            }))


def cooking_process(cook, stoves: queue.Queue, ovens: queue.Queue, food_items: queue.PriorityQueue):
    while True:
        try:
            item = food_items.get_nowait()
            food_item = item[2]
            curr_counter = item[1]
            food_details = next((f for f in menu if f['id'] == food_item['food_id']), None)
            (idx, order_details) = next(((idx, order) for idx, order in enumerate(orders) if order['order_id'] == food_item['order_id']), (None, None))
            len_order_items = len(orders[idx]['items'])
            # check if cook can afford to do this type of food
            if food_details['complexity'] == cook['rank'] or food_details['complexity'] == cook['rank'] - 1:
                cooking_aparatus = food_details['cooking-apparatus']
                if cooking_aparatus is None:
                    print(f'{threading.current_thread().name} cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} manually')
                    time.sleep(food_details['preparation-time'] * time_unit)
                    print(
                        f'{threading.current_thread().name}  finished cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} manually')
                elif cooking_aparatus == 'oven':
                    oven = ovens.get_nowait()
                    print(f'{threading.current_thread().name} cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on oven {oven} ')
                    time.sleep(food_details['preparation-time'] * time_unit)
                    length = ovens.qsize()
                    ovens.put_nowait(length)
                    print(
                        f'{threading.current_thread().name} finished cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on oven {oven} ')
                elif cooking_aparatus == 'stove':
                    stove = stoves.get_nowait()
                    print(f'{threading.current_thread().name} cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on stove {stove} ')
                    time.sleep(food_details['preparation-time'] * time_unit)
                    length = stoves.qsize()
                    stoves.put_nowait(length)
                    print(
                        f'{threading.current_thread().name}  finished cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on stove {stove} ')


                orders[idx]['prepared_items'] += 1
                if orders[idx]['prepared_items'] == len_order_items:
                    print(f'{threading.current_thread().name} cook has finished the order {order_details["order_id"]}')
                    orders[idx]['cooking_details'].put({'food_id': food_details['id'], 'cook_id': cook['id']})
                    finish_preparation_time = int(time.time())
                    print(f'Calculating')
                    payload = {
                        **orders[idx],
                        'cooking_time': finish_preparation_time - int(orders[idx]['received_time']),
                        'cooking_details': list(orders[idx]['cooking_details'].queue)
                    }
                    requests.post('http://localhost:3000/distribution', json=payload, timeout=0.0000000001)



            else:
                food_items.put_nowait((food_item['priority'], curr_counter, food_item))

        except Exception as e:
            pass


def cooks_multitasking_process(cook, ovens, stoves, food_items):
    for i in range(cook['proficiency']):
        task_thread = threading.Thread(target=cooking_process, args=(cook, ovens, stoves, food_items,), daemon=True, name=f'{cook["name"]}-Task {i}')
        task_thread.start()


def run_kitchen_server():
    main_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=3030, debug=False, use_reloader=False), daemon=True)
    main_thread.start()

    for _, cook in enumerate(restaurant_cooks):
        cook_thread = threading.Thread(target=cooks_multitasking_process, args=(cook,ovens_q,stoves_q, foods_q,), daemon=True)
        cook_thread.start()

    while True:
        pass

if __name__ == '__main__':
    run_kitchen_server()