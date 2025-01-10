ORM-модели и pydantic-схемы для "спаршенных" аккаунтов LinkedIn пользователей Платформы.

БД: таблицы:
1. linkedin_profiles (есть связь на таблицу Users (из common_db))
2. linkedin_experience - work experience entries (связь на linkedin_profiles)
3. linkedin_education - education entries (связь на linkedin_profiles)

pydantic: для чтения кортежей из БД юзать схему LinkedInProfileRead
