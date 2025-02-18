# Диаграммы LinkedIn Verifier Service

Для визуализации диаграмм используйте [Mermaid Live Editor](https://mermaid.live/)

## Процесс обработки профилей

```mermaid
flowchart TB
    Start([Start]) --> Input[/"Входные данные:<br>CSV или PubSub"/]
    
    subgraph "Валидация входных данных"
        Input --> ValidateURL["Валидация LinkedIn URL<br><i>validate_linkedin_username()</i>"]
        ValidateURL --> ExtractUser["Извлечение username<br>из URL"]
    end
    
    subgraph "Получение данных"
        ExtractUser --> API["Запрос к LinkedIn API<br><i>get_profile()</i>"]
        API --> SaveRaw["Сохранение RAW данных<br><i>save_raw_data()</i>"]
    end
    
    subgraph "Валидация и сохранение"
        SaveRaw --> ValidateWork["Проверка опыта работы<br><i>validate_work_experience()</i>"]
        ValidateWork --> CheckTarget{"Найдена<br>целевая<br>компания?"}
        CheckTarget -->|Да| SetFlags["Установка флагов:<br>is_target_company_found<br>is_employee_in_target_company"]
        CheckTarget -->|Нет| NoTarget["Сброс флагов<br>целевой компании"]
        
        SetFlags & NoTarget --> CheckExists{"Профиль<br>существует?"}
        
        CheckExists -->|Да| UpdateProfile["Обновление профиля:<br>1. Основные данные<br>2. Добавление нового опыта<br>3. Добавление образования"]
        CheckExists -->|Нет| CreateProfile["Создание профиля:<br>1. Основные данные<br>2. Опыт работы<br>3. Образование"]
    end
    
    UpdateProfile & CreateProfile --> NotifyCurator["Уведомление куратора<br>через PubSub"]
    NotifyCurator --> End([End])

    %% Контрастная цветовая схема
    classDef process fill:#663399,stroke:#333,stroke-width:2px,color:#fff;
    classDef storage fill:#004d99,stroke:#333,stroke-width:2px,color:#fff;
    classDef validation fill:#994d00,stroke:#333,stroke-width:2px,color:#fff;
    classDef api fill:#006600,stroke:#333,stroke-width:2px,color:#fff;
    classDef default fill:#fff,stroke:#333,stroke-width:1px,color:#000;
    
    class ValidateURL,ValidateWork,CheckTarget validation;
    class SaveRaw,UpdateProfile,CreateProfile storage;
    class API api;
    class NotifyCurator process;
    class Input,ExtractUser,SetFlags,NoTarget,CheckExists default;
```

## Структура базы данных

```mermaid
erDiagram
    ORMUserProfile ||--o{ ORMLinkedInProfile : has
    ORMLinkedInProfile ||--o{ ORMLinkedInEducation : has
    ORMLinkedInProfile ||--o{ ORMLinkedInWorkExperience : has
    
    ORMUserProfile {
        int id PK
        string username UK "Уникальный ключ"
        bool is_verified "Should be here!"
    }

    ORMLinkedInProfile {
        %% Ключи и основные поля
        int id PK
        string public_identifier UK "LinkedIn ID"
        string username FK "-> UserProfile"
        
        %% Базовая информация
        string linkedin_url "Профиль"
        string first_name "Имя"
        string last_name "Фамилия"
        
        %% Текущая работа (денормализовано)
        bool is_currently_employed "Денормализовано"
        string current_company_label "Из последнего опыта"
        string current_position_title "Из последнего опыта"
        
        %% Валидация целевой компании
        bool is_target_company_found "Найдена"
        bool is_employee_in_target_company "Текущий сотрудник"
        string target_company_label "Название"
        
        %% Проблемное поле
        bool is_verified "Move to UserProfile!"
        
        %% Аудит
        datetime updated_at
        datetime created_at
    }

    ORMLinkedInEducation {
        int id PK
        int profile_id FK "-> Profile"
        string school_name "Название"
        string degree_name "Степень"
        date start_date "Начало"
        date end_date "Конец"
    }

    ORMLinkedInWorkExperience {
        int id PK
        int profile_id FK "-> Profile"
        string company_label "Компания"
        string title "Должность"
        date start_date "Начало"
        date end_date "Конец"
    }

    ORMLinkedInRawData {
        int id PK
        string target_linkedin_url UK "LinkedIn URL"
        jsonb raw_data "JSON от API"
        timestamp parsed_date "Дата парсинга"
    }

    ORMLinkedInApiLimits {
        int id PK
        string provider_type "SCRAPIN/TOMQUIRK"
        string provider_id "API key/email"
        int credits_left "Осталось кредитов"
        int rate_limit_left "Осталось запросов"
    }
```

## Архитектура сервиса

```mermaid
flowchart TB
 subgraph Inputs["Inputs"]
        Parser["Profile Parser"]
        CSV["CSV File<br>Manual Testing"]
        Main["main.py"]
        PubSub["PubSub<br>Production"]
  end
 subgraph subGraph1["API Providers"]
        ScrapinRepo["Scrapin Repository<br>scrapin.io"]
        Factory["Repository Factory"]
        TomQuirkRepo["TomQuirk Repository<br>linkedin-api"]
  end
 subgraph subGraph2["LinkedIn Service"]
        Service["LinkedIn Service<br><i>Core Component</i>"]
        Validator["Data Validator"]
        WorkValidator["Work Experience<br>Validator"]
        subGraph1
        DBManager["DB Manager"]
  end
 subgraph subGraph3["Database Layer"]
        RawDB[("Raw Data<br>Storage")]
        ProfileDB[("Profile<br>Storage")]
        LimitsDB[("API Limits<br>Storage")]
  end
    CSV --> Parser
    PubSub --> Main
    Main --> Service
    Parser --> Service
    Service --> Validator & Factory & DBManager & n2["PubSub Notifier<br>"]
    Validator --> WorkValidator
    Factory -- SCRAPIN --> ScrapinRepo
    Factory -- TOMQUIRK --> TomQuirkRepo
    ScrapinRepo -- External API --> LinkedIn[("LinkedIn")]
    TomQuirkRepo -- External API --> LinkedIn
    DBManager -- Raw Data --> RawDB
    DBManager -- Validated --> ProfileDB
    DBManager -- Limits --> LimitsDB

    %% Контрастная цветовая схема для архитектуры
    style Service fill:#663399,stroke:#333,stroke-width:4px,color:#fff
    style Validator fill:#994d00,stroke:#333,color:#fff
    style WorkValidator fill:#994d00,stroke:#333,color:#fff
    style Parser fill:#fff,stroke:#333,color:#000
    style Main fill:#fff,stroke:#333,color:#000
    style Factory fill:#fff,stroke:#333,color:#000
    style DBManager fill:#004d99,stroke:#333,color:#fff
    style n2 fill:#663399,stroke:#333,color:#fff
```

## Процесс валидации профиля

```mermaid
stateDiagram-v2
    [*] --> ValidateUsername
    ValidateUsername --> GetProfile: Valid
    ValidateUsername --> Error: Invalid

    GetProfile --> SaveRawData: Success
    GetProfile --> Error: API Error

    SaveRawData --> ValidateWorkExperience: Success
    SaveRawData --> Error: DB Error

    ValidateWorkExperience --> SaveProfile: Done
    SaveProfile --> [*]: Success
    SaveProfile --> Error: DB Error

    Error --> [*]
```

## Поток данных

```mermaid
flowchart TD
    A[CSV File] -->|Read| B(Raw LinkedIn URLs)
    B -->|Validate| C{Valid URL?}
    C -->|Yes| D[Extract Username]
    C -->|No| E[Log Error]
    D -->|API Request| F{Mock Mode?}
    F -->|Yes| G[Mock Data]
    F -->|No| H[Real API Data]
    G -->|Validate| I[Process Profile]
    H -->|Validate| I
    I -->|Save| J[(Database)]
    I -->|Update| K[API Limits]
```

## Как использовать диаграммы

1. Скопируйте код диаграммы между тегами ` ```mermaid ` и ` ``` `
2. Вставьте в [Mermaid Live Editor](https://mermaid.live/)
3. Редактируйте и экспортируйте по необходимости

## Дополнительные ресурсы

- [Документация Mermaid](https://mermaid.js.org/intro/)
- [Примеры диаграмм](https://mermaid.js.org/syntax/examples.html)

## Процесс валидации опыта работы

```mermaid
flowchart TB
    Start([Start]) --> CheckInput{"Есть данные<br>профиля?"}
    CheckInput -->|Нет| SetDefault["Установка значений<br>по умолчанию:<br>is_target_company_found = False<br>positions_count = 0"]
    
    CheckInput -->|Да| CheckExp{"Есть опыт<br>работы?"}
    CheckExp -->|Нет| SetDefault
    
    CheckExp -->|Да| FindTarget["Поиск позиций<br>в целевой компании"]
    
    FindTarget --> HasTarget{"Найдены<br>позиции?"}
    HasTarget -->|Нет| SetDefault
    
    HasTarget -->|Да| Process["Обработка позиций"]
    
    subgraph "Анализ опыта работы"
        Process --> Sort["Сортировка по дате<br><i>от новых к старым</i>"]
        Sort --> Latest["Получение последней<br>позиции в компании"]
        Latest --> SetFields["Установка полей профиля:<br>- target_company_label<br>- target_position_title<br>- target_company_linkedin_id<br>- target_company_linkedin_url"]
        SetFields --> CheckCurrent{"Текущая<br>работа?"}
        CheckCurrent -->|Да| SetEmployee["is_employee_in_target_company = True"]
        CheckCurrent -->|Нет| UnsetEmployee["is_employee_in_target_company = False"]
    end
    
    SetEmployee & UnsetEmployee --> SetFound["is_target_company_found = True<br>positions_count = количество позиций"]
    SetFound --> End([End])
    SetDefault --> End

    %% Контрастная цветовая схема для валидации опыта
    classDef process fill:#663399,stroke:#333,stroke-width:2px,color:#fff;
    classDef check fill:#994d00,stroke:#333,stroke-width:2px,color:#fff;
    classDef data fill:#004d99,stroke:#333,stroke-width:2px,color:#fff;
    classDef default fill:#fff,stroke:#333,stroke-width:1px,color:#000;
    
    class CheckInput,CheckExp,HasTarget,CheckCurrent check;
    class Process,Sort,Latest process;
    class SetFields,SetFound,SetDefault,SetEmployee,UnsetEmployee data;
```

%% Примечания:
%% 1. Поиск позиций в целевой компании учитывает регистр (toLowerCase)
%% 2. Сортировка использует безопасную дату для null значений (1900-01-01)
%% 3. Все изменения полей профиля происходят в памяти до сохранения в БД 