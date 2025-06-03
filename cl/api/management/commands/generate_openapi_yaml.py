import pathlib

from django.core.management.base import BaseCommand
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiYamlRenderer


class Command(BaseCommand):
    help = "Generates OpenAPI schema in YAML format and saves it to a file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            "-f",
            default="openapi.yaml",
            help="The output file path for the OpenAPI YAML schema.",
        )
        parser.add_argument(
            "--api-version",
            "-av",
            default="v4",
            help="The API version to generate the schema for (e.g., v3, v4).",
        )
        parser.add_argument(
            "--api-filter-path",
            "-p",
            default=None,
            help="The path to filter the API paths by (e.g., /api/rest).",
        )

    def handle(self, *args, **options):
        output_file_path_str = options["file"]
        api_version = options["api_version"]
        api_filter_path = options["api_filter_path"]

        output_file_path = pathlib.Path(output_file_path_str)

        self.stdout.write(
            f"Generating OpenAPI schema for API version: {api_version}..."
        )

        if api_filter_path:
            self.stdout.write(f"Filtering API paths by: {api_filter_path}")

        def filter_endpoints_by_path(endpoints):
            if not api_filter_path:
                return endpoints
            filtered_endpoints = []
            for path, path_regex, method, callback in endpoints:
                if path.startswith(api_filter_path):
                    filtered_endpoints.append((path, path_regex, method, callback))
            return filtered_endpoints

        try:
            generator = SchemaGenerator(
                api_version=api_version,
                preprocessing_hooks=[filter_endpoints_by_path]
            )
            schema = generator.get_schema(request=None, public=True)
            # OpenApiYamlRenderer is a class, not an instance taking schema.
            # Its render method takes the schema data as the first argument.
            renderer = OpenApiYamlRenderer()
            yaml_output = renderer.render(data=schema, renderer_context={})

            with open(output_file_path, "wb") as f:
                f.write(yaml_output)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated OpenAPI YAML schema to: {output_file_path}"
                )
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Error generating OpenAPI schema: {e}")
            )
