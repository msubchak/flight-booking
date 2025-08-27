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


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "position")


class CrewListSerializer(CrewSerializer):
    position = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


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


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "departure_time", "arrival_time", "route", "airplane")


class FlightListSerializer(serializers.ModelSerializer):
    route = serializers.SerializerMethodField()
    airplane = AirplaneListSerializer(read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)
    duration = serializers.SerializerMethodField()
    crews = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = (
            "id",
            "departure_time",
            "arrival_time",
            "route",
            "duration",
            "crews",
            "airplane",
            "tickets_available"
        )

    def get_route(self, obj):
        return f"{obj.route.source.name} -> {obj.route.destination.name}"

    def get_duration(self, obj):
        duration = obj.arrival_time - obj.departure_time
        total_minutes = int(abs(duration.total_seconds()) // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"

    def get_crews(self, obj):
        return f"{obj.crews.count()}"


class FlightRetrieveSerializer(FlightListSerializer):
    crews = CrewListSerializer(read_only=True, many=True)
    taken_seats = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = (
            "id",
            "departure_time",
            "arrival_time",
            "route",
            "duration",
            "airplane",
            "crews",
            "taken_seats"
        )

    def get_taken_seats(self, obj):
        seats = {}
        for ticket in obj.tickets.all():
            seats.setdefault(ticket.row, []).append(ticket.seat)
        return {row: sorted(seats_list) for row, seats_list in seats.items()}


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ("id", "name")


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "create_at", "user")


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
