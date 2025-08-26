from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import (
    Flight,
    Crew,
    Position,
    Ticket,
    Order,
    Airplane,
    AirplaneType,
    Route,
    Airport,
    City,
    Country
)


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "airplane", "departure_time", "arrival_time", "crews")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "position")


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ("id", "name")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "order")

    def validate(self, attrs):
        Ticket.validate_value(
            attrs["seat"],
            attrs["flight"].airplane.seats_in_row,
            "seat",
            serializers.ValidationError
        )
        Ticket.validate_value(
            attrs["row"],
            attrs["flight"].airplane.rows,
            "row",
            serializers.ValidationError
        )
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "create_at", "user")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type")


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "city")


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "country")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name")
