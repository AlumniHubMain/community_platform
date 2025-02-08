class Staff:
    def __init__(self,
                 telegram_id: int,
                 telegram_name: str,
                 name: str,
                 is_admin: bool,
                 is_notified) -> None:
        self.telegram_id = telegram_id
        self.telegram_name = telegram_name
        self.name = name
        self.is_admin = is_admin
        self.is_notified = is_notified


admitted_people: dict[int, Staff] = {347684159: Staff(telegram_id=347684159,
                                                      telegram_name='BBigInt',
                                                      name='Серёга',
                                                      is_admin=True,
                                                      is_notified=True),
                                     298401179: Staff(telegram_id=298401179,
                                                      telegram_name='kravttt',
                                                      name='Миша',
                                                      is_admin=True,
                                                      is_notified=True),
                                     1368810473: Staff(telegram_id=1368810473,
                                                       telegram_name='os_babushkina',
                                                       name='Оля',
                                                       is_admin=True,
                                                       is_notified=False)}

notified_people: list[int] = [i for i in admitted_people if admitted_people[i].is_notified is True]
