"""Swagger: ochiq API ko'rinishlari serializer'siz yozilgan — javob umumiy JSON obyekt sifatida ko'rsatiladi, teglar manzildan."""
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes


class TaggedAutoSchema(AutoSchema):
    def get_tags(self) -> list[str]:
        tags = super().get_tags()
        path = self.path
        if path.startswith('/api/site/'):
            return ['Sayt (Payload mos)']
        if path.startswith('/api/me'):
            return ['Xodim kabineti']
        if path.startswith('/api/auth/hemis'):
            return ['HEMIS']
        if path.startswith('/api/cms/'):
            return tags
        return ['Sayt API']

    def get_response_serializers(self):
        return super().get_response_serializers() or OpenApiTypes.OBJECT

    def get_request_serializer(self):
        return super().get_request_serializer() or (OpenApiTypes.OBJECT if self.method in ('POST', 'PUT', 'PATCH') else None)
