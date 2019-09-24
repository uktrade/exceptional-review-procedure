from rest_framework import serializers


class CompaniesHouseSearchSerializer(serializers.Serializer):
    term = serializers.CharField()
