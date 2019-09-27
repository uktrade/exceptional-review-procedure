from rest_framework import serializers


class CompaniesHouseSearchSerializer(serializers.Serializer):
    term = serializers.CharField()


class CommodityCodeSearchSerializer(serializers.Serializer):
    term = serializers.CharField()


