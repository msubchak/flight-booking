from django.db.models import Count, F, Prefetch
from django.utils.dateparse import parse_date
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from rest_framework.viewsets import GenericViewSet

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
from core.permissions import IsAdminOrIfAuthenticatedReadOnly
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
    AirplaneListSerializer,
    FlightListSerializer,
    FlightRetrieveSerializer,
)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]


    def get_queryset(self):
        queryset = self.queryset

        departure_city = self.request.query_params.get("departure_city")
        arrival_city =  self.request.query_params.get("arrival_city")
        departure_date = self.request.query_params.get("departure_date")

        if departure_city:
            queryset = queryset.filter(route__source__city__name__icontains=departure_city)

        if arrival_city:
            queryset = queryset.filter(route__destination__city__name__icontains=arrival_city)

        if departure_date:
            date_obj = parse_date(departure_date)
            if date_obj:
                queryset = queryset.filter(departure_time__date=date_obj)


        if self.action == "list":
            queryset = (
                queryset
                .select_related(
                    "airplane__airplane_type",
                    "route__source__city__country",
                    "route__destination__city"
                )
                .annotate(
                    tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets",
                                                                                                distinct=True),
                    crew_count=Count("crews", distinct=True)
                )
            )
        if self.action == "retrieve":
            queryset = (
                queryset
                .select_related(
                    "airplane__airplane_type",
                    "route__source__city__country",
                    "route__destination__city"
                )
                .prefetch_related(
                    "crews__position",
                    "tickets__order"
                )
            )
        return queryset


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CrewListSerializer
        return CrewSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("position")
        return queryset


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related(
                "flight__airplane",
                "flight__route__source__city__country",
                "flight__route__destination__city__country",
                "order__user"
            ).prefetch_related(
                "flight__crews"
            )
        return queryset


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_staff:
            queryset = queryset
        else:
            queryset = queryset.filter(user=self.request.user)
        Ticket_queryset = Ticket.objects.select_related(
            "flight__airplane",
            "flight__route__source__city__country",
            "flight__route__destination__city__country",
        )
        queryset = queryset.prefetch_related(
            Prefetch("tickets", queryset=Ticket_queryset),
        ).select_related("user")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AirplaneListSerializer
        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("airplane_type")
        return queryset


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related(
                "source__city__country",
                "destination__city__country"
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteListSerializer
        return RouteSerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("city__country")
        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AirportListSerializer
        return AirportSerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("country")
        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CityListSerializer
        return CitySerializer


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
