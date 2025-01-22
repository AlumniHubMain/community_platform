import asyncio
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue as MPQueue
from threading import Thread
from time import sleep

from loguru import logger

from app.data_extractor.extractor import VacancyExtractor
from app.db import VacancyRepository


class VacancyProcessor:
    """Processes vacancy URLs using multiple extractors and a queue."""

    def __init__(self, vacancy_repository: VacancyRepository, num_workers: int = 3, logger: logger = logger) -> None:
        """Initialize the processor with multiple parser workers.

        Args:
            vacancy_repository: Repository for vacancy operations
            num_workers: Number of parser worker processes
            logger: Logger instance
        """
        self.logger = logger
        self.url_queue = MPQueue()
        self.data_queue = MPQueue()
        self.parser_workers: list[Process] = []
        self.repository = vacancy_repository
        self.num_workers = num_workers

        # Start parser workers
        self.logger.info(f"Starting {self.num_workers} vacancy parser processes")
        for i in range(self.num_workers):
            process = Process(
                target=self._process_urls_wrapper,
                name=f"ParserWorker-{i}",
                args=(self.url_queue, self.data_queue),
            )
            process.start()
            self.parser_workers.append(process)

    def _process_data_thread(self) -> None:
        """Process and save data from the data queue in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            try:
                if self.data_queue.empty():
                    sleep(10)
                    continue

                url, company_name, data = self.data_queue.get_nowait()
                if url is None:  # Poison pill
                    self.logger.info("Data processor thread received shutdown signal")
                    break

                self.logger.debug(f"Saving data for URL: {url}")
                try:
                    self.repository.add_or_update(url, company_name, data)
                    self.logger.info(f"Successfully saved data for URL: {url}")

                except Exception as db_error:
                    self.logger.error(f"Database error while saving data for URL {url}: {str(db_error)}")

            except Exception as e:
                self.logger.exception(f"Error processing data queue: {str(e)}")
                sleep(0.1)

        loop.close()
        self.logger.info("Data processor thread shutdown complete")

    async def start(self) -> None:
        """Start processing the data queue."""
        self.logger.info("Processor already started in __init__")

        # Start data processor thread
        self.logger.info("Starting data processor thread")
        self.data_processor = Thread(target=self._process_data_thread, name="DataProcessor", daemon=True)
        self.data_processor.start()

    async def shutdown(self) -> None:
        """Shutdown the processor and wait for all processes to complete."""
        self.logger.info("Initiating vacancy processor shutdown")
        self._running = False

        # Send poison pills to parser workers
        self.logger.debug("Sending shutdown signal to parser workers")
        for _ in self.parser_workers:
            self.url_queue.put((None, None))  # Poison pill

        # Wait for parser workers to finish
        self.logger.debug("Waiting for parser workers to shutdown")
        for process in self.parser_workers:
            process.join()

        # Send poison pill to data processor
        self.logger.debug("Sending shutdown signal to data processor")
        self.data_queue.put((None, None, None))  # Poison pill

        # Wait for data processor thread to finish
        self.logger.debug("Waiting for data processor thread to shutdown")
        self.data_processor.join()

        self.logger.info("Vacancy processor shutdown complete")

    @staticmethod
    def _process_urls_wrapper(url_queue: MPQueue, data_queue: MPQueue) -> None:
        """Wrapper method to run the async _process_urls in a separate process."""
        logger.info(f"Starting process: {multiprocessing.current_process().name}")
        asyncio.run(VacancyProcessor._process_urls_static(url_queue, data_queue))

    @staticmethod
    async def _process_urls_static(url_queue: MPQueue, data_queue: MPQueue) -> None:
        """Static version of _process_urls to run in separate process."""
        worker_name = multiprocessing.current_process().name
        logger.info(f"Starting process: {worker_name}")

        extractor = VacancyExtractor(logger=logger)

        while True:
            try:
                url, company_name = url_queue.get()
                if url is None:  # Poison pill
                    logger.info(f"Process {worker_name} received shutdown signal")
                    break

                logger.debug(f"Process {worker_name} processing URL: {url}")
                vacancy_data = await extractor.process_vacancy(url)

                if vacancy_data:
                    logger.debug(f"Process {worker_name} saving vacancy data for URL: {url}")
                    data_queue.put((url, company_name, vacancy_data))
                    logger.info(f"Process {worker_name} successfully processed vacancy: {url}")
                else:
                    logger.warning(f"Process {worker_name} could not extract data from URL: {url}")

            except Exception as e:
                logger.exception(f"Process {worker_name} encountered error processing URL: {str(e)}")

        logger.info(f"Process {worker_name} shutdown complete")

    async def add_url(self, url: str, company_name: str) -> None:
        """Add single URL to the processing queue."""
        self.logger.debug(f"Adding URL to queue: {url}")
        self.url_queue.put((url, company_name))
