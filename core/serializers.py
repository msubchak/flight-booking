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
    position = serializers.CharField(source="position.name", read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="flight.route.source.name", read_only=True)
    destination = serializers.CharField(source="flight.route.destination.name", read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "source", "destination", "order")


class TicketCreateSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="flight.route.source.name", read_only=True)
    destination = serializers.CharField(source="flight.route.destination.name", read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "flight", "row", "seat", "source", "destination")

    def validate(self, attrs):
        Ticket(
            row=attrs["row"],
            seat=attrs["seat"],
            flight=attrs["flight"],
        ).check_constraints(serializers.ValidationError)
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "create_at", "tickets")
        read_only_fields = ("user",)

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    departure_airport = serializers.CharField(source="source.name")
    arrival_airport = serializers.CharField(source="destination.name")
    departure_country = serializers.CharField(source="source.city.country.name", read_only=True)
    departure_city = serializers.CharField(source="source.city.name", read_only=True)
    arrival_country = serializers.CharField(source="destination.city.country.name", read_only=True)
    arrival_city = serializers.CharField(source="destination.city.name", read_only=True)

    class Meta:
        model = Route
        fields = (
            "id",
            "departure_airport",
            "arrival_airport",
            "departure_country",
            "departure_city",
            "arrival_country",
            "arrival_city",
            "distance",
        )


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "departure_time", "arrival_time", "route", "airplane")


class FlightListSerializer(serializers.ModelSerializer):
    route = RouteListSerializer(read_only=True)
    airplane = AirplaneListSerializer(read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)
    duration = serializers.SerializerMethodField()
    crews = serializers.IntegerField(read_only=True, source="crew_count")

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

    def get_duration(self, obj):
        duration = obj.arrival_time - obj.departure_time
        total_minutes = int(duration.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"


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
        return {row: sorted(seats_list) for row, seats_list in sorted(seats.items())}


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ("id", "name")


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
