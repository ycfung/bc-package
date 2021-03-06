import hashlib
import json

from sawtooth_sdk.processor.exceptions import InternalError


PC_NAMESPACE = hashlib.sha512('pacel_chain'.encode("utf-8")).hexdigest()[0:6]

USER_NAMEPCACE = hashlib.sha512('user_state'.encode("utf-8")).hexdigest()[0:4]
ORDER_NAMESPACE = hashlib.sha512('order_state'.encode("utf-8")).hexdigest()[0:4]


CONFIG_ADDRESS = PC_NAMESPACE

def make_user_address(public_key):
    return PC_NAMESPACE + USER_NAMEPCACE + public_key[-60:]

def make_order_address(order_number):
    return PC_NAMESPACE + ORDER_NAMESPACE + hashlib.sha512(order_number.encode("utf-8")).hexdigest()[-60:]

def make_station_address(station):
    return PC_NAMESPACE + hashlib.sha512(station.encode('utf-8')).hexdigest()[-64:]

def make_mobile_address(mobile):
    return PC_NAMESPACE + hashlib.sha512(mobile.encode('utf-8')).hexdigest()[-64:]


SETTING_ADDRESS = PC_NAMESPACE + "0000000000000000000000000000000000000000000000000000000000000000"


class MobileState:
    def __init__(self,context):
        self._context = context
        self.TIMEOUT = 3
        self._address_cache = {}

    def get_state(self,mobile):
        address = make_mobile_address(mobile)
        if address in self._address_cache:
            return self._address_cache[address]

        datas = self._context.get_state([address])
        if datas == []:
            return None
        else:
            return json.loads(datas[0].data.decode())

    def add_order(self,mobile,order_numbers):
        address = make_mobile_address(mobile)

        if address in self._address_cache:
            state = self._address_cache[address]
        else:
            state = self.get_state(mobile)
            if state is None:
                state = {'order_number':[],'accepted_order_number':[]}

        order_numbers.extend(state['order_number'])
        state['order_number'] = order_numbers

        self._address_cache[address] = state
        self._context.set_state({address:json.dumps(state).encode()},timeout = self.TIMEOUT)

    def add_accepted_order(self,mobile,order_numbers):

        address = make_mobile_address(mobile)

        if address in self._address_cache:
            state = self._address_cache[address]
        else:
            state = self.get_state(mobile)
            if state is None:
                state = {'order_number': [], 'accepted_order_number': []}

        order_numbers.extend(state['accepted_order_number'])
        state['accepted_order_number'] = order_numbers
        self._address_cache[address] = state
        self._context.set_state({address: json.dumps(state).encode()}, timeout=self.TIMEOUT)

class StationState:

    def __init__(self,context):
        self._context = context
        self.TIMEOUT = 3
        self._address_cache = {}

    def get_state(self,station):
        address = make_station_address(station)

        if address in self._address_cache:
            return self._address_cache[address]

        datas = self._context.get_state([address])

        if datas == []:
            return None
        else:
            return json.loads(datas[0].data.decode())

    def add_key(self,station,pub_key):

        address = make_station_address(station)


        state = self.get_state(station)
        if state is None:
            state = {'keys':[]}

        state['keys'].append(pub_key)
        self._address_cache[address] = state

        self._context.set_state({address:json.dumps(state).encode()},timeout=self.TIMEOUT)

    def check_authority(self,station,pub_key):

        address = make_station_address(station)

        state = self.get_state(station)

        if state is None:
            return False

        if pub_key not in state['keys']:
            return False
        else:
            return True

class SettingState:
    def __init__(self,context):
        self._context  = context
        self.TIMEOUT = 3
        self._address_cache = None

    def get_state(self):
        if self._address_cache is not None:
            return self._address_cache
        else:
            datas = self._context.get_state([SETTING_ADDRESS])
            if datas != []:
                return json.loads(datas[0].data.decode())
            else:
                return None

    def set_inited_key(self,pub_key):
        state_json = self.get_state()


        if state_json is None:
            state_json = {}
        if 'inited' in state_json:
            if state_json['inited']:
                return False

        state_json['inited'] = True
        state_json['inited_key'] = pub_key


        self._address_cache = state_json
        self._context.set_state({SETTING_ADDRESS:json.dumps(state_json).encode()},timeout = self.TIMEOUT)

        return True

    def get_admin_key(self):
        state_json = self.get_state()

        if state_json is not None:
           return state_json['inited_key']
        else:
            return None

class UserState:

    def __init__(self, context):
        self._context  = context
        self.TIMEOUT = 3
        self._address_cache = {}

    def get_state(self,public_key):

        address = make_user_address(public_key)

        if address in self._address_cache:
            data = self._address_cache[address]
        else:
            datas = self._context.get_state([address])
            if datas:
                data = json.loads(datas[0].data.decode())
            else:
                return None

        return data

    def add_coin(self,pub_key,coin):
        address = make_user_address(pub_key)
        data = self.get_state(pub_key)
        if data is None:
            return False
        else:
            data['coin'] += coin
            self._context.set_state({address:json.dumps(data).encode()},timeout = self.TIMEOUT)
            return True

    def subtract_coin(self,pub_key,coin):

        address = make_user_address(pub_key)
        data = self.get_state(pub_key)

        if data is None:
            return False
        else:
            data['coin'] -= coin
            if data['coin'] < 0:
                return False

            self._context.set_state({address: json.dumps(data).encode()}, timeout=self.TIMEOUT)
            return True

    def set_state(self,public_key,coin,mobile):
        address = make_user_address(public_key)
        data = {'key':public_key,'coin':coin,'mobile':mobile}
        self._address_cache[address] = data
        self._context.set_state({address:json.dumps(data).encode()},timeout = self.TIMEOUT)


class OrderState:


    def __init__(self,context):
        self._context = context
        self.TIMEOUT = 3
        self._address_cache = {}

    def get_order(self,order_number):
        address = make_order_address(order_number)
        if address in self._address_cache:
            return self._address_cache[address]
        else:
            datas = self._context.get_state([address],timeout = self.TIMEOUT)
            if datas:
                order = json.loads(datas[0].data.decode())
                return order
            else:
                return None

    def _set_order(self, order):

        address = make_order_address(order['order_number'])

        self._address_cache[address] = order
        self._context.set_state({address:json.dumps(order).encode()},timeout = self.TIMEOUT)

    def set_order_state(self,order_number,state):
        order =  self.get_order(order_number)
        if order is None:
            return False
        else:
            order['state'] = state

        self._set_order(order)

        return True

#    def create_order(self,order_number, initiator,accepter,station,destination,pacel_number,coin):

    def create_order(self,order_number, station ,pacel_number):

        if self.get_order(order_number) is not None:
            return False

        order = {'order_number':order_number,'station':station,
                 'pacel_number':pacel_number,'state':'init'}
        self._set_order(order)

        return True

    def apply_order(self,order_number,coin,destionation):

        order = self.get_order(order_number)

        if order is None:
            return False

        if order['state'] != 'init':
            return False
        else:
            order['coin'] = coin
            order['destionation'] = destionation
            order['state'] = 'apply'

        self._set_order(order)

        return True

    def accept_order(self,order_number,acceptor):

        order = self.get_order(order_number)

        if order is None:
            return False

        if order['state']!= 'apply':
            return False

        else:
            order['acceptor'] = acceptor
            order['state'] = 'accepted'

        self._set_order(order)

        return True


    def delete_order(self,order_number):
        address = make_order_address(order_number)
        if self._address_cache[address]:
            del self._address_cache[address]

        self._context.delete_state([address],timeout = self.TIMEOUT)

##################################################################### use json



'''old version without using json

class User:

    def __init__(self,coins,mobile):
        self.coin = coins
        self.mobile = mobile


class UserState:

    def __init__(self, context):
        self._context  = context
        self.TIMEOUT = 3
        self._address_cache = {}


    def get_state(self,public_key):

        address = make_user_address(public_key)

        if address in self._address_cache:
            data = self._address_cache[address]
        else:
            datas = self._context.get_state([address])
            if datas:
                data = datas[0].data.decode()
            else:
                return None

        coins_str,mobile = data.decode().split(',')
        coins = int(coins_str)
        return User(coins,mobile)


    def set_state(self,public_key,user):
        address = make_user_address(public_key)
        data = (str(user.coin)+','+str(user.mobile)).encode()
        self._address_cache[address] = data
        self._context.set_state({address:data},timeout = self.TIMEOUT)







class Order:

    def __init__(self,order_number,initiator,accepter,station,destination,pacel_number,coin,state):
        self.order_number = order_number
        self.initiator = initiator
        self.acceptor = accepter
        self.station = station
        self.destination = destination
        self.pacel_number = pacel_number
        self.coin = coin
        self.state = state


class OrderState:


    def __init__(self,context):
        self._context = context
        self.TIMEOUT = 3

        self._address_cache = {}


    def create_order(self,order_number, initiator,accepter,station,destination,pacel_number,coin):
        order = Order(order_number, initiator,accepter,station,destination,pacel_number,coin,'apply')
        self.set_order(order)


    def set_order(self, order):
        address = make_oder_address(order.order_number)

        data = self._serialize(order)
        self._address_cache[address] = data
        self._context.set_state({address:data},timeout = self.TIMEOUT)


    def get_order(self,order_number):
        address = make_oder_address(order_number)
        if address in self._address_cache:
            order = self._deserialize( self._address_cache[address] )
            return order
        else:
            serialize_orders = self._context.get_state([address],timeout = self.TIMEOUT)
            if serialize_orders:
                serialize_order = serialize_orders[0].data
                order = self._deserialize(serialize_order)
                return order
            else:
                return None

    def delete_order(self,order_number):
        address = make_oder_address(order_number)
        if self._address_cache[address]:
            del self._address_cache[address]

        self._context.delete_state([address],timeout = self.TIMEOUT)




    def _deserialize(self,data):
        order_str = data.decode()
        order_number,initiator,accepter,station,destination,pacel_number,coin,state = order_str.split(",")
        return Order(order_number,initiator,accepter,station,destination,pacel_number,int(coin),state)

    def _serialize(self,order):
        order_str = ",".join([order.order_number,order.initiator,order.acceptor,order.station,order.destination,
                              order.pacel_number,str(order.coin),order.state])
        return order_str.encode()

'''
