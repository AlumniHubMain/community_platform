import asyncio

from loguru import logger

from app.data_extractor import VacancyExtractor

if __name__ == "__main__":
    logger.info("Checking vacancies")
    urls = [
        "https://wargaming.com/en/careers/vacancy_3022040_warsaw/",
        "https://wargaming.com/en/careers/vacancy_3013800_belgrade/",
    ]
    extractor = VacancyExtractor(logger=logger)
    results = asyncio.run(extractor.process_vacancies(urls))
    logger.info(results)
