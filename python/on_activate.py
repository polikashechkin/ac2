import os, sys

from domino.core import log
from domino.account import find_account_id

from _system.databases import Postgres
import _system.tables.postgres.account

import tables.postgres

import procs.cleaning

if __name__ == "__main__":
    try:
        account_id = find_account_id(sys.argv[1])
        if account_id is None:
            print (f'Не найдена учетная запись "{sys.argv[1]}"')
            sys.exit(1)
    except Exception as ex:
        print(f'Не задана учетная запись : {ex}')
        sys.exit(1)

    Postgres.on_activate(account_id, print)
    procs.cleaning.on_activate(account_id, print)

