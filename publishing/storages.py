from os import path

from storages.backends.s3boto3 import S3Boto3Storage


class LoadingReportStorage(S3Boto3Storage):
    def get_default_settings(self):
        # Importing settings here makes it possible for tests to override_settings
        from django.conf import settings

        return dict(
            super().get_default_settings(),
            bucket_name=settings.LOADING_REPORTS_BUCKET_NAME,
            access_key=settings.LOADING_REPORTS_S3_ACCESS_KEY_ID,
            secret_key=settings.LOADING_REPORTS_S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.LOADING_REPORTS_S3_ENDPOINT_URL,
            default_acl="private",
        )

    def generate_filename(self, filename: str) -> str:
        from django.conf import settings

        filename = path.join(
            settings.LOADING_REPORTS_STORAGE_DIRECTORY,
            filename,
        )
        return super().generate_filename(filename)

    def get_object_parameters(self, name):
        self.object_parameters.update(
            {"ContentDisposition": f"attachment; filename={path.basename(name)}"},
        )
        return super().get_object_parameters(name)
