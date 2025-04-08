import atexit
import os

from opentelemetry import metrics
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


class VacanciesMonitoring:
    """Metrics for monitoring vacancy parsing."""

    def __init__(self, name: str, instance_id: str | None = None):
        self.last_update_success = True

        instance_id = instance_id if instance_id else os.getenv("CLOUD_RUN_EXECUTION")

        # Create metric readers with buffering
        metric_readers = [
            PeriodicExportingMetricReader(
                CloudMonitoringMetricsExporter(add_unique_identifier=False),
                export_interval_millis=1000,  # 1 second
                export_timeout_millis=1000,  # 1 second timeout
            ),
            # Add console exporter for debugging
            PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=1000,
            ),
        ]

        self.meter_provider = MeterProvider(
            metric_readers=metric_readers,
            resource=Resource.create({
                "service.name": "vacancy-parser",
                "service.namespace": "vacancies",
                "service.instance.id": instance_id,
            }),
        )

        metrics.set_meter_provider(self.meter_provider)
        self.meter = metrics.get_meter(name)
        self._init_metrics()

        # Register shutdown handler
        atexit.register(self.shutdown)

    def shutdown(self):
        """Force flush metrics before shutdown."""
        if self.meter_provider:
            self.meter_provider.shutdown()

    def _init_metrics(self):
        # Number of new vacancies parsed
        self.new_vacancies_gauge = self.meter.create_gauge(
            name="new_vacancies_gauge",
            unit="1",
            description="Number of new vacancies parsed from each site",
        )

        # Total number of active vacancies on a site
        self.active_vacancies_gauge = self.meter.create_gauge(
            name="active_vacancies_gauge",
            unit="1",
            description="Total number of active vacancies on each site",
        )

        self.input_tokens_counter = self.meter.create_counter(
            name="input_tokens_counter",
            unit="1",
            description="Number of input tokens used",
        )

        self.output_tokens_counter = self.meter.create_counter(
            name="output_tokens_counter",
            unit="1",
            description="Number of output tokens used",
        )

        self.total_tokens_counter = self.meter.create_counter(
            name="total_tokens_counter",
            unit="1",
            description="Number of total tokens used",
        )

    def record_parsing_session(self, site_name: str, active_vacancies: int, new_vacancies: int):
        """Record metrics for a completed parsing session for a specific site.

        Args:
            site_name: Name of the site that was parsed
            active_vacancies: Total number of active vacancies on the site
            new_vacancies: Number of new vacancies successfully parsed
            unparsed_vacancies: Number of new vacancies that could not be parsed
        """
        attributes = {"site": site_name}

        self.active_vacancies_gauge.set(active_vacancies, attributes)
        self.new_vacancies_gauge.set(new_vacancies, attributes)

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

        self.input_tokens_counter.add(prompt_tokens, attributes)
        self.output_tokens_counter.add(completion_tokens, attributes)
        self.total_tokens_counter.add(total_tokens, attributes)


monitoring = VacanciesMonitoring(name="vacancy_parser", instance_id=os.environ.get("CLOUD_RUN_EXECUTION"))
