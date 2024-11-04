CREATE TABLE if not exists users
(
    created_at                              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	
    id                                      BIGSERIAL PRIMARY KEY,

    name                                    VARCHAR(100) NOT NULL,
    surname                                 VARCHAR(100) NOT NULL,
    email                                   VARCHAR(200) NOT NULL,

    avatars                                 VARCHAR(300)[], -- сделаем список. Наверняка захотим иметь множество Аватарок.

    city_live                               VARCHAR(200),
    country_live                            VARCHAR(100),
    phone_number                            VARCHAR(20),
    linkedin_link                           VARCHAR(100),

    telegram_name                           VARCHAR(200),
    telegram_id                             BIGINT,

    -- workplaces                              BIGSERIAL[], -- ?? храним массив айдишников с "записями в трудовой", чтобы быстро селектить по основному ключу

    requests_to_society                     VARCHAR(100)[],
    professional_interests                  VARCHAR(100)[]

    -- mentor_id                            BIGSERIAL, -- ?? айдишник с записью о менторстве. Кажется, логично вытащить это в отдельную таблицу
    -- mentee_id                            BIGSERIAL, -- ?? то же самое, только про менти
    --?? помечены айдишники в сторонних таблицах. Возможно, нам хватит использовать те же айдишники в этих таблицах, чтобы
);

