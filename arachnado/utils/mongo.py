from six.moves.urllib.parse import urlparse

import motor


_CLIENT_CACHE = {}


def motor_from_uri(uri):
    parsed = urlparse(uri)
    client_args = parsed.netloc, parsed.port
    client = _CLIENT_CACHE.get(
        client_args,
        motor.MotorClient(*client_args)
    )
    db_name, col_name = parsed.path.split('/')[1:]
    db = client[db_name]
    col = db[col_name]

    return client, db_name, db, col_name, col
