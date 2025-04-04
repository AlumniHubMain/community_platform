import logging
import os
import time
from typing import Optional

from opentelemetry import metrics
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


class VacanciesMonitoring:
    """Metrics for monitoring vacancy parsing."""

    def __init__(self, name: str, logger: logging.Logger, instance_id: Optional[str] = None):
        self.logger = logger
        self.last_update_success = True

        instance_id = instance_id if instance_id else os.getenv("CLOUD_RUN_EXECUTION")

        metrics.set_meter_provider(
            MeterProvider(
                metric_readers=[
                    PeriodicExportingMetricReader(
                        CloudMonitoringMetricsExporter(add_unique_identifier=False),
                        export_interval_millis=5000,
                    )
                ],
                resource=Resource.create({
                    "service.name": "vacancy-parser",
                    "service.namespace": "vacancies",
                    "service.instance.id": instance_id,
                }),
            )
        )
        self.meter = metrics.get_meter(name)
        self._init_metrics()

    def _init_metrics(self):
        # Number of new vacancies parsed
        self.new_vacancies_counter = self.meter.create_counter(
            name="new_vacancies_counter",
            unit="1",
            description="Number of new vacancies parsed from each site",
        )

        # Total number of active vacancies on a site
        self.active_vacancies_gauge = self.meter.create_gauge(
            name="active_vacancies_gauge",
            unit="1",
            description="Total number of active vacancies on each site",
        )

        # Number of unparsed new vacancies
        self.unparsed_vacancies_counter = self.meter.create_counter(
            name="unparsed_vacancies_counter",
            unit="1",
            description="Number of vacancies that could not be parsed",
        )

        # Parsing duration metrics
        self.parsing_duration_histogram = self.meter.create_histogram(
            name="parsing_duration",
            unit="ms",
            description="Time taken to parse vacancies from each site",
        )

        # Parsing failures counter
        self.parsing_failures_counter = self.meter.create_counter(
            name="parsing_failures_counter",
            unit="1",
            description="Number of parsing failures for each site",
        )

        # Token usage by model and site
        self.token_usage_counter = self.meter.create_counter(
            name="token_usage_counter",
            unit="1",
            description="Number of tokens used for LLM processing",
        )

    def record_parsing_session(
        self, site_name: str, active_vacancies: int, new_vacancies: int, unparsed_vacancies: int
    ):
        """Record metrics for a completed parsing session for a specific site.

        Args:
            site_name: Name of the site that was parsed
            active_vacancies: Total number of active vacancies on the site
            new_vacancies: Number of new vacancies successfully parsed
            unparsed_vacancies: Number of new vacancies that could not be parsed
        """
        attributes = {"site": site_name}

        if active_vacancies >= 0:
            self.active_vacancies_gauge.set(active_vacancies, attributes)
            self.logger.info(
                f"Active vacancies on {site_name}: {active_vacancies}",
                extra={"site": site_name, "count": active_vacancies},
            )

        if new_vacancies > 0:
            self.new_vacancies_counter.add(new_vacancies, attributes)
            self.logger.info(
                f"Parsed {new_vacancies} new vacancies from {site_name}",
                extra={"site": site_name, "count": new_vacancies},
            )

        if unparsed_vacancies > 0:
            self.unparsed_vacancies_counter.add(unparsed_vacancies, attributes)
            self.logger.info(
                f"Failed to parse {unparsed_vacancies} vacancies from {site_name}",
                extra={"site": site_name, "count": unparsed_vacancies},
            )

    def record_parsing_duration(self, site_name: str, start_time: float):
        """Record the time taken to parse vacancies from a site."""
        duration_ms = (time.time() - start_time) * 1000
        self.parsing_duration_histogram.record(duration_ms, {"site": site_name})
        self.logger.info(
            f"Parsing from {site_name} took {duration_ms:.2f}ms", extra={"site": site_name, "duration_ms": duration_ms}
        )

    def record_parsing_failure(self, site_name: str, error: Exception):
        """Record a parsing failure for a site."""
        self.parsing_failures_counter.add(1, {"site": site_name, "error_type": type(error).__name__})
        self.logger.error(
            f"Failed to parse vacancies from {site_name}: {str(error)}",
            extra={"site": site_name, "error": str(error)},
            exc_info=True,
        )

    def record_token_usage(self, site_name: str, prompt_tokens: int, completion_tokens: int, model: str = "gemini"):
        """Record the token usage for LLM processing for a specific site.

        Args:
            site_name: Name of the site being processed
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            model: Name of the model used
        """
        total_tokens = prompt_tokens + completion_tokens
        attributes = {"site": site_name, "model": model}

        self.token_usage_counter.add(prompt_tokens, {**attributes, "type": "prompt"})
        self.token_usage_counter.add(completion_tokens, {**attributes, "type": "completion"})
        self.token_usage_counter.add(total_tokens, {**attributes, "type": "total"})

        self.logger.info(
            "Token usage for {site_name}: {prompt_tokens} prompt, {completion_tokens} completion, {total_tokens} total with {model}",
            extra={
                "site": site_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "model": model,
            },
        )

    def track_site_parsing(self, site_name: str, func):
        """Decorator to track a complete parsing session including timing and error handling.

        This decorator will time the parsing function and record all metrics for the site.
        """

        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # Assume the function returns a tuple of (new_vacancies, active_vacancies, unparsed_vacancies)
                result = func(*args, **kwargs)

                # Handle different return formats
                if isinstance(result, tuple) and len(result) >= 3:
                    new_vacancies, active_vacancies, unparsed_vacancies = result[0], result[1], result[2]
                    self.record_parsing_session(
                        site_name=site_name,
                        active_vacancies=active_vacancies,
                        new_vacancies=new_vacancies,
                        unparsed_vacancies=unparsed_vacancies,
                    )

                self.record_parsing_duration(site_name, start_time)
                return result
            except Exception as e:
                self.record_parsing_failure(site_name, e)
                raise

        return wrapper
