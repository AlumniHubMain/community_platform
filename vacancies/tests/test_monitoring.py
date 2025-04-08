# vacancies/tests/test_real_gcp_monitoring.py
# ПРЕДУПРЕЖДЕНИЕ: Этот тест отправляет реальные данные в Google Cloud Monitoring.
# НЕ ИСПОЛЬЗУЙТЕ ЕГО В РЕГУЛЯРНОМ CI/CD.
# Запускайте только вручную для специфических проверок интеграции.
# Убедитесь, что ваша среда аутентифицирована в GCP с правами записи метрик.

import os
import time
import uuid
from unittest.mock import patch

import pytest

# Класс под тестом
from app.config.monitoring import VacanciesMonitoring

# Уникальный ID для этого тестового запуска, чтобы попытаться изолировать метрики
# (хотя они все равно попадут в общий поток)
TEST_RUN_INSTANCE_ID = f"test-run-{uuid.uuid4()}"


@pytest.fixture(scope="module")
def real_monitoring_instance(pytestconfig):
    """
    Создает экземпляр VacanciesMonitoring, который будет пытаться
    отправить данные в реальный GCP Monitoring.
    Мокируем только atexit.
    """

    # Получаем проект из окружения (может быть установлено gcloud)
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT", "communityp-440714")
    print(f"\nПРЕДУПРЕЖДЕНИЕ: Этот тест отправит метрики в проект GCP: {gcp_project}")
    print(f"Идентификатор тестового запуска (service.instance.id): {TEST_RUN_INSTANCE_ID}")

    # Мокируем только atexit, чтобы не регистрировать реальный shutdown handler
    with patch("app.config.monitoring.atexit"):
        instance = VacanciesMonitoring(name="test_parser_real_gcp", instance_id=TEST_RUN_INSTANCE_ID)
        yield instance
        # Важно: даем время на экспорт перед завершением фикстуры/теста.
        # PeriodicExportingMetricReader экспортирует по интервалу (10 сек в коде).
        # force_flush() может не работать надежно с Periodic reader.
        print("\nОжидание потенциальной отправки метрик в GCP (15 секунд)...")
        time.sleep(15)
        print("Попытка принудительной отправки...")
        # Попытка принудительной отправки, хотя она не гарантирована для Periodic reader
        try:
            if instance.meter_provider:
                # Доступ к внутреннему provider для shutdown
                instance.meter_provider.shutdown()
                print("MeterProvider shutdown вызван.")
        except Exception as e:
            print(f"Ошибка при вызове shutdown: {e}")


def test_send_parsing_session_to_gcp(real_monitoring_instance: VacanciesMonitoring):
    """
    Тест отправки метрик сессии парсинга в реальный GCP Monitoring.
    ПРОВЕРКА РЕЗУЛЬТАТА ДОЛЖНА ВЫПОЛНЯТЬСЯ ВРУЧНУЮ В GCP CONSOLE!
    """
    site_name = "real-gcp-test.com"
    active_vacancies = 999
    new_vacancies = 11

    print(f"\nОтправка метрик сессии парсинга для сайта: {site_name}")
    real_monitoring_instance.record_parsing_session(site_name, active_vacancies, new_vacancies)
    print("Вызов record_parsing_session выполнен.")
    # Даем немного времени на внутреннюю обработку перед завершением теста
    # (хотя основной экспорт происходит по интервалу)
    time.sleep(3)
    # Реальная проверка должна быть выполнена вручную в Google Cloud Monitoring Console,
    # ища метрики с `service.instance.id = TEST_RUN_INSTANCE_ID` и `site = site_name`.


def test_send_token_usage_to_gcp(real_monitoring_instance: VacanciesMonitoring):
    """
    Тест отправки метрик использования токенов в реальный GCP Monitoring.
    ПРОВЕРКА РЕЗУЛЬТАТА ДОЛЖНА ВЫПОЛНЯТЬСЯ ВРУЧНУЮ В GCP CONSOLE!
    """
    site_name = "real-gcp-test.org"
    prompt_tokens = 555
    completion_tokens = 44

    print(f"\nОтправка метрик токенов для сайта: {site_name}")
    real_monitoring_instance.record_token_usage(site_name, prompt_tokens, completion_tokens)
    print("Вызов record_token_usage выполнен.")
    # Даем немного времени на внутреннюю обработку
    time.sleep(2)
    # Реальная проверка должна быть выполнена вручную в Google Cloud Monitoring Console,
    # ища метрики с `service.instance.id = TEST_RUN_INSTANCE_ID`, `site = site_name` и `model = model`.
