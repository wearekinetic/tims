
class MessageException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class GeocodingException(MessageException):
    pass


class LineException(MessageException):
    def __init__(self, message, line, line_no):
        super().__init__(message)
        self.line = line
        self.line_no = line_no

    def __str__(self):
        return f'Error - \n{self.message} on line {self.line_no}\n\n{self.line}'


class ParserException(LineException):
    pass


class TimeException(LineException):
    pass