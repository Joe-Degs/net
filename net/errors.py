class Error(Exception):
    def __init__(self, message):
        super().__init__(message)

class SocketError(Error):
    def __init__(self, reason: str):
        super().__init__(f'socket: {reason}')

class AddressError(Error):
    def __init__(self, expression, reason):
        super().__init__(f'address: {expression} - {reason}')

class UnknownNetworkError(Error):
    def __init__(self, network: str):
        super().__init__(f'unkown network {network}')
