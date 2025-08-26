from rest_framework import viewsets

from core.models import (
    Flight,
    Crew,
    Position,
    Ticket,
    Order,
    Airport,
    AirplaneType,
    Route,
    City,
    Country,
    Airplane
)
from core.serializers import (
    FlightSerializer,
    CrewSerializer,
    PositionSerializer,
    TicketSerializer,
    OrderSerializer,
    AirplaneSerializer,
    AirplaneTypeSerializer,
    RouteSerializer,
    AirportSerializer,
    CitySerializer,
    CountrySerializer,
    CrewListSerializer,
    CityListSerializer,
    AirportListSerializer,
    RouteListSerializer,
    AirplaneListSerializer, FlightListSerializer,
)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class  = FlightSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return FlightListSerializer
        return FlightSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CrewListSerializer
        return CrewSerializer


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AirplaneListSerializer
        return AirplaneSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteListSerializer
        return RouteSerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AirportListSerializer
        return AirportSerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CityListSerializer
        return CitySerializer


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
