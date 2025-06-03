import pathlib
import shutil
import tempfile
import yaml
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.urls import path, re_path
from django.test import TestCase, override_settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.routers import SimpleRouter

# Dummy API Views for testing
class TestView1(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"message": "Test view 1"})

class TestView2(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"message": "Test view 2"})

class TestView3(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"message": "Test view 3"})

# Dummy URL patterns for testing
# We define urlpatterns directly in a list, and then point ROOT_URLCONF to this module.
# This is a common pattern for testing Django apps with dynamic URLs.

router = SimpleRouter()
# router.register r'api/rest/v1/test1' , TestView1, basename='test1' # This won't work as desired for specific paths
# router.register r'api/rest/v2/test2' , TestView2, basename='test2'
# router.register r'api/other/test3' , TestView3, basename='test3'

# For drf-spectacular to pick up specific paths as defined,
# it's often better to use django.urls.path or re_path directly for test setup.
# However, drf-spectacular's management command usually discovers views from the default router
# or by inspecting applications listed in INSTALLED_APPS and their routers.
# For simplicity and direct control in tests, we'll define explicit paths.

urlpatterns = [
    path('api/rest/v1/test1/', TestView1.as_view(), name='test1'),
    path('api/rest/v2/test2/', TestView2.as_view(), name='test2'),
    path('api/other/test3/', TestView3.as_view(), name='test3'),
]

@override_settings(ROOT_URLCONF=__name__) # Point to this module's urlpatterns
class GenerateOpenApiYamlTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_file_path = pathlib.Path(self.temp_dir) / "openapi_test.yaml"
        # Ensure SPECTACULAR_SETTINGS are minimal to avoid interference from project settings
        self.base_spectacular_settings = {
            'TITLE': 'Test API',
            'VERSION': '1.0.0',
            'SERVE_INCLUDE_SCHEMA': False, # Don't include the schema view itself
            # We will use the PREPROCESSING_HOOKS from the command itself.
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_generate_openapi_yaml_no_filter(self):
        with override_settings(SPECTACULAR_SETTINGS=self.base_spectacular_settings):
            call_command(
                "generate_openapi_yaml",
                file=str(self.output_file_path),
                api_version="v1", # This version is used by SchemaGenerator but not directly by our dummy views here
                stdout=StringIO(), # Suppress output
                stderr=StringIO(), # Suppress errors
            )

        self.assertTrue(self.output_file_path.exists())
        with open(self.output_file_path, "r") as f:
            schema = yaml.safe_load(f)

        self.assertIn("paths", schema)
        paths = schema["paths"]
        self.assertIn("/api/rest/v1/test1/", paths)
        self.assertIn("/api/rest/v2/test2/", paths)
        self.assertIn("/api/other/test3/", paths)

    def test_generate_openapi_yaml_with_filter(self):
        with override_settings(SPECTACULAR_SETTINGS=self.base_spectacular_settings):
            call_command(
                "generate_openapi_yaml",
                file=str(self.output_file_path),
                api_version="v1",
                api_filter_path="/api/rest",
                stdout=StringIO(),
                stderr=StringIO(),
            )

        self.assertTrue(self.output_file_path.exists())
        with open(self.output_file_path, "r") as f:
            schema = yaml.safe_load(f)

        self.assertIn("paths", schema)
        paths = schema["paths"]
        self.assertIn("/api/rest/v1/test1/", paths)
        self.assertIn("/api/rest/v2/test2/", paths)
        self.assertNotIn("/api/other/test3/", paths)

    def test_generate_openapi_yaml_with_filter_no_match(self):
        with override_settings(SPECTACULAR_SETTINGS=self.base_spectacular_settings):
            call_command(
                "generate_openapi_yaml",
                file=str(self.output_file_path),
                api_version="v1",
                api_filter_path="/api/nonexistent",
                stdout=StringIO(),
                stderr=StringIO(),
            )

        self.assertTrue(self.output_file_path.exists())
        with open(self.output_file_path, "r") as f:
            schema = yaml.safe_load(f)

        # Depending on drf-spectacular's behavior with empty paths after filtering:
        # Option 1: "paths" key is present but empty
        # self.assertIn("paths", schema)
        # self.assertEqual(len(schema["paths"]), 0)
        # Option 2: "paths" key might be omitted if no paths are found (less likely for valid schema)
        # self.assertNotIn("paths", schema)
        # For now, let's assume paths is present and empty, or not present.
        # If it's present and empty, that's fine. If it's not present, that's also fine for this test.
        self.assertEqual(schema.get("paths", {}), {}, "Paths should be empty or absent when filter matches nothing.")

    def test_generate_openapi_yaml_api_version_parameter(self):
        # Test that the api_version parameter is passed to SchemaGenerator
        # We can't directly inspect SchemaGenerator's call, but we can check if the command runs
        # and produces a schema. The actual filtering of versions by SchemaGenerator is out of scope
        # for this specific command's tests, but we ensure the parameter is accepted.
        custom_settings = self.base_spectacular_settings.copy()
        custom_settings['SCHEMA_PATH_PREFIX'] = '/api/{version}/' # Example setting that might use api_version

        with override_settings(SPECTACULAR_SETTINGS=custom_settings):
            call_command(
                "generate_openapi_yaml",
                file=str(self.output_file_path),
                api_version="v2", # Test with a different version
                stdout=StringIO(),
                stderr=StringIO(),
            )
        self.assertTrue(self.output_file_path.exists())
        # Further checks could involve inspecting parts of the schema that might change with api_version
        # if the dummy views or SPECTACULAR_SETTINGS were more complex.
        # For now, just ensuring it runs and creates a file is sufficient to test parameter passthrough.
        with open(self.output_file_path, "r") as f:
            schema = yaml.safe_load(f)
        self.assertIn("info", schema)
        # If SCHEMA_PATH_PREFIX used {version}, drf-spectacular might incorporate it.
        # However, the command passes `api_version` to SchemaGenerator, which then uses it.
        # The command itself doesn't directly use api_version to alter paths before SchemaGenerator.
        # A simple check:
        self.assertIn("paths", schema) # Ensure some paths are generated
        # The version in schema['info']['version'] is from SPECTACULAR_SETTINGS['VERSION'], not api_version param.
        self.assertEqual(schema['info']['version'], '1.0.0')

# Ensure Django discovers these urlpatterns for the tests
# This is usually handled by @override_settings(ROOT_URLCONF=__name__)
# or by ensuring this module is part of a discoverable app's urls.py
# when running tests for that app.
# The @override_settings on the class should handle this.
if settings.configured and __name__ == settings.ROOT_URLCONF:
    pass # URLs are correctly configured for tests
elif not settings.configured:
    # This block is more for standalone script execution context, less for Django test runner
    settings.configure(ROOT_URLCONF=__name__, INSTALLED_APPS=['rest_framework', 'drf_spectacular', __name__.split('.')[0]]) # Minimal settings
    import django
    django.setup()

# Note: For the schema generator to pick up on these views, the app
# containing this test module (e.g., 'cl.api') would typically need to be in INSTALLED_APPS.
# If it's not, drf-spectacular might not find these views.
# The @override_settings(ROOT_URLCONF=__name__) is the primary mechanism here.
# For more complex scenarios, a dedicated test app in INSTALLED_APPS might be needed.
# Let's assume 'cl.api' or a relevant app is in INSTALLED_APPS for the test environment.
# We also need 'drf_spectacular' in INSTALLED_APPS.
# These are usually handled by the main project's test settings.
