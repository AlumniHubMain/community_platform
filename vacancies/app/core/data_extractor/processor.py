import asyncio
import multiprocessing
import traceback
from multiprocessing import Process
from multiprocessing import Queue as MPQueue
from threading import Thread
from time import sleep

import picologging
import picologging.config
from picologging import Logger

from app.config import logger_config
from app.core.data_extractor.extractor import VacancyExtractor
from app.db import VacancyRepository


class VacancyProcessor:
    """Processes vacancy URLs using multiple extractors and a queue."""

    def __init__(
        self,
        vacancy_repository: VacancyRepository,
        max_input_tokens: int = 1_000_000,
        max_output_tokens: int = 1_000_000,
        num_workers: int = 3,
        logger: Logger = Logger,
    ) -> None:
        """Initialize the processor with multiple parser workers.

        Args:
            vacancy_repository: Repository for vacancy operations
            max_input_tokens: Maximum number of input tokens to use
            max_output_tokens: Maximum number of output tokens to use
            num_workers: Number of parser worker processes
            logger: Logger instance
            monitoring: Monitoring instance
        """
        self.logger = logger
        self.url_queue = MPQueue()
        self.data_queue = MPQueue()
        self.parser_workers: list[Process] = []
        self.repository = vacancy_repository
        self.num_workers = num_workers
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens

        # Start parser workers
        self.logger.info("Starting vacancy parser processes", extra={"num_workers": self.num_workers})
        for i in range(self.num_workers):
            process = Process(
                target=self._process_urls,
                name=f"ParserWorker-{i}",
                args=(
                    self.url_queue,
                    self.data_queue,
                    max_input_tokens / self.num_workers,
                    max_output_tokens / self.num_workers,
                ),
                daemon=True,
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

                self.logger.debug(
                    {
                        "message": "Saving data for URL",
                        "url": url,
                    },
                )
                try:
                    self.repository.add_or_update(url, company_name, data)
                    self.logger.info(
                        {
                            "message": "Successfully saved data for URL",
                            "url": url,
                        },
                    )

                except Exception:
                    self.logger.error(
                        {
                            "message": "Database error while saving data for URL",
                            "url": url,
                            "error": traceback.format_exc(),
                        },
                    )

            except Exception:
                self.logger.exception(
                    {
                        "message": "Error processing data queue",
                        "error": traceback.format_exc(),
                    },
                )
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
    def _process_urls(url_queue: MPQueue, data_queue: MPQueue, max_input_tokens: int, max_output_tokens: int) -> None:
        """Process URLs in a separate process using async extractor."""
        worker_name = multiprocessing.current_process().name
        picologging.config.dictConfig(logger_config(worker_name))
        logger = picologging.getLogger(worker_name)

        async def process_urls_async():
            extractor = VacancyExtractor(
                logger=logger,
                max_input_tokens=max_input_tokens,
                max_output_tokens=max_output_tokens,
            )

            while True:
                try:
                    url, company_name = url_queue.get()
                    if url is None:  # Poison pill
                        logger.info(
                            {
                                "message": "Process received shutdown signal",
                                "worker_name": worker_name,
                            },
                        )
                        break

                    logger.debug(
                        {
                            "message": "Process processing URL",
                            "url": url,
                            "worker_name": worker_name,
                        },
                    )
                    vacancy_data = await extractor.process_vacancy(url, company_name)
                    worker_input_tokens, worker_output_tokens = extractor.get_current_tokens()

                    if vacancy_data:
                        logger.debug(
                            {
                                "message": "Process saving vacancy data for URL",
                                "url": url,
                                "worker_name": worker_name,
                            },
                        )
                        data_queue.put((url, company_name, vacancy_data))
                        logger.info(
                            {
                                "message": "Process successfully processed vacancy",
                                "url": url,
                                "worker_name": worker_name,
                                "input_tokens": worker_input_tokens,
                                "output_tokens": worker_output_tokens,
                            },
                        )
                    else:
                        logger.warning(
                            {
                                "message": "Process could not extract data from URL",
                                "url": url,
                                "worker_name": worker_name,
                                "worker_input_tokens": worker_input_tokens,
                                "worker_output_tokens": worker_output_tokens,
                            },
                        )

                    if worker_input_tokens <= 0 or worker_output_tokens <= 0:
                        logger.warning(
                            {
                                "message": "Process has no tokens left, shutting down",
                                "worker_name": worker_name,
                                "worker_input_tokens": worker_input_tokens,
                                "worker_output_tokens": worker_output_tokens,
                            },
                        )
                        break

                    total_input_tokens, total_output_tokens = extractor.get_current_tokens()

                    return max_input_tokens - total_input_tokens, max_output_tokens - total_output_tokens

                except Exception:
                    logger.exception(
                        {
                            "message": "Process encountered error processing URL",
                            "error": traceback.format_exc(),
                            "worker_name": worker_name,
                        },
                    )

            logger.info(
                {
                    "message": "Process shutdown complete",
                    "worker_name": worker_name,
                },
            )

        asyncio.run(process_urls_async())

    async def add_url(self, url: str, company_name: str) -> None:
        """Add single URL to the processing queue."""
        self.logger.debug(
            {
                "message": "Adding URL to queue",
                "url": url,
            },
        )
        self.url_queue.put((url, company_name))
