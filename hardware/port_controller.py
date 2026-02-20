import serial


class PortController:
    def __init__(self, port, *, baud = 9600, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1):
        # Replace port with the correct port and '9600' with the correct baud rate
        self.ser = serial.Serial(
            port=port,
            baudrate=baud,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
            timeout=timeout
        )

    def write(self, data, encoding= 'utf-8'):
        """Write `data` to port using `encoding`"""
        self.ser.write(data.encode(encoding))

    def read(self, size = 1):
        """Reads `size` bytes. Sanitize data before use."""
        return self.ser.read(size)

class DebugPortController:
    def __init__(self, port, *, baud = 9600, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1):
        ...

    def write(self, data, encoding= 'utf-8'):
        """Write `data` to port using `encoding`"""
        print("Writing to port:", data)