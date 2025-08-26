from django.db import models

from flight_booking import settings


class Flight(models.Model):
    route = models.ForeignKey("Route", on_delete=models.PROTECT)
    airplane = models.ForeignKey("Airplane", on_delete=models.PROTECT)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crews = models.ManyToManyField("Crew", related_name="flights")

    def __str__(self):
        return f"Flight {self.id}, {self.route} {self.departure_time} -> {self.arrival_time}"


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.ForeignKey("Position", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.position}"


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("flight", "row", "seat",)

    @staticmethod
    def validate_value(value: int, max_value: int, field_name: str, error_to_raise):
        if not (1 <= value <= max_value):
            raise error_to_raise(
                {
                    field_name: f"{field_name} must be in range [1, {max_value}], not {value}"
                }
            )

    def clean(self):
        airplane = self.flight.airplane
        Ticket.validate_value(self.seat, airplane.seats_in_row, "seat", ValueError)
        Ticket.validate_value(self.row, airplane.rows, "row",ValueError)

    def __str__(self):
        return f"Ticket {self.row}{self.seat} for {self.flight}"


class Order(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Order {self.id} by {self.user} on {self.create_at}"


class Airplane(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey("AirplaneType", on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class AirplaneType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey("Airport", related_name="routes_from", on_delete=models.PROTECT)
    destination = models.ForeignKey("Airport", on_delete=models.PROTECT, related_name="routes_to")
    distance = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="unique_route",
            )
        ]

    def __str__(self):
        return f"{self.source} -> {self.destination}. Distance {self.distance}km"


class Airport(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.ForeignKey("City", on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=255, unique=True)
    country = models.ForeignKey("Country", on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
