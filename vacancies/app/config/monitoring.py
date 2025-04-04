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
        self.new_vacancies_counter = self.meter.create_counter(
            name="new_vacancies_counter",
            unit="1",
            description="Number of new vacancies parsed from each site",
        )

        self.total_vacancies_gauge = self.meter.create_gauge(
            name="total_vacancies_gauge",
            unit="1",
            description="Total number of vacancies available on each site",
        )

        self.parsing_duration_histogram = self.meter.create_histogram(
            name="parsing_duration",
            unit="ms",
            description="Time taken to parse vacancies from each site",
        )

        self.parsing_failures_counter = self.meter.create_counter(
            name="parsing_failures_counter",
            unit="1",
            description="Number of parsing failures for each site",
        )

        self.token_usage_counter = self.meter.create_counter(
            name="token_usage_counter",
            unit="1",
            description="Number of tokens used for LLM processing",
        )

    def record_new_vacancies(self, site_name: str, count: int):
        """Record the number of new vacancies parsed from a site."""
        if count <= 0:
            return

        self.new_vacancies_counter.add(count, {"site": site_name})
        self.logger.info(f"Parsed {count} new vacancies from {site_name}", extra={"site": site_name, "count": count})

    def record_total_vacancies(self, site_name: str, count: int):
        """Record the total number of vacancies available on a site."""
        if count < 0:
            return

        self.total_vacancies_gauge.set(count, {"site": site_name})
        self.logger.info(
            f"Total vacancies available on {site_name}: {count}", extra={"site": site_name, "count": count}
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

    def record_token_usage(self, prompt_tokens: int, completion_tokens: int, model: str = "gemini"):
        """Record the token usage for LLM processing.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            model: Name of the model used
        """
        total_tokens = prompt_tokens + completion_tokens
        self.token_usage_counter.add(prompt_tokens, {"type": "prompt", "model": model})
        self.token_usage_counter.add(completion_tokens, {"type": "completion", "model": model})
        self.token_usage_counter.add(total_tokens, {"type": "total", "model": model})

        self.logger.info(
            f"Token usage: {prompt_tokens} prompt, {completion_tokens} completion, {total_tokens} total for {model}",
            extra={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "model": model,
            },
        )

    def track_parsing_session(self, site_name: str, func):
        """Decorator to track a complete parsing session including timing and error handling."""

        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                if isinstance(result, tuple) and len(result) >= 2:
                    new_vacancies, total_vacancies = result[0], result[1]
                    self.record_new_vacancies(site_name, new_vacancies)
                    self.record_total_vacancies(site_name, total_vacancies)
                self.record_parsing_duration(site_name, start_time)
                return result
            except Exception as e:
                self.record_parsing_failure(site_name, e)
                raise

        return wrapper
