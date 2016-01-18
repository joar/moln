class BencodeError(Exception):
    pass


class DecodeError(BencodeError):
    pass


class EncodeError(BencodeError):
    pass
