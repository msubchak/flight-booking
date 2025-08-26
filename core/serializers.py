from rest_framework import serializers

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
        fields = ("id", "airplane", "departure_time", "arrival_time", "route")


class FlightListSerializer(FlightSerializer):
    route = serializers.SerializerMethodField()

    def get_route(self, obj):
        return f"{obj.route.source.name} -> {obj.route.destination.name}"


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "position")


class CrewListSerializer(CrewSerializer):
    position = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


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


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True
    )


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )
    destination = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )
    country = serializers.CharField(
        source="source.city.country.name",
        read_only=True,
    )
    city = serializers.CharField(
        source="destination.city.name",
        read_only=True,
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance", "country", "city")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "city")


class AirportListSerializer(serializers.ModelSerializer):
    city = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )
    country = serializers.CharField(
        source="city.country.name",
        read_only=True,
    )

    class Meta:
        model = Airport
        fields = ("id", "name", "country", "city")


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "country")


class CityListSerializer(CitySerializer):
    country = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name")
