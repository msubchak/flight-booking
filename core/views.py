from django.db.models import Count, F, Prefetch
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

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
    AirplaneImageSerializer,
    FlightCreateUpdateSerializer,
)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightCreateUpdateSerializer

    def get_queryset(self):
        queryset = self.queryset

        departure_city = self.request.query_params.get("departure_city")
        arrival_city = self.request.query_params.get("arrival_city")
        departure_date = self.request.query_params.get("departure_date")
        arrival_date = self.request.query_params.get("arrival_date")

        if departure_city:
            queryset = (queryset.filter
                        (route__source__city__name__icontains=departure_city)
                        )

        if arrival_city:
            queryset = queryset.filter(
                route__destination__city__name__icontains=arrival_city
            )

        if departure_date:
            date_obj = parse_date(departure_date)
            if date_obj:
                queryset = queryset.filter(departure_time__date=date_obj)

        if arrival_date:
            date_obj = parse_date(arrival_date)
            if date_obj:
                queryset = queryset.filter(arrival_time__date=date_obj)

        if self.action == "list":
            queryset = (
                queryset
                .select_related(
                    "airplane__airplane_type",
                    "route__source__city__country",
                    "route__destination__city__country",
                )
                .prefetch_related(
                    "crews__position",
                )
                .annotate(
                    tickets_available=(
                            F("airplane__seats_in_row") * F("airplane__rows")
                            - Count("tickets", distinct=True)
                    ),
                    crew_count=Count("crews", distinct=True),
                )
            )
        if self.action == "retrieve":
            queryset = (
                queryset
                .select_related(
                    "airplane__airplane_type",
                    "route__source__city__country",
                    "route__destination__city__country"
                )
                .prefetch_related(
                    "crews__position",
                    "tickets__order__user"
                )
            )
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "departure_city",
                type=str,
                description=(
                        "Filter flights departing from this city"
                        " (ex. ?departure_city=Warszawa)"
                ),
                required=False,
            ),
            OpenApiParameter(
                "arrival_city",
                type=str,
                description=(
                        "Filter flights arriving to this city"
                        " (ex. ?arrival_city=Lviv)"
                ),
            ),
            OpenApiParameter(
                "departure_date",
                type=str,
                description=(
                        "Filter flights by departure date"
                        " (ex. ?departure_date=2025-08-30)"
                ),
            ),
            OpenApiParameter(
                "arrival_date",
                type=str,
                description=(
                        "Filter flights by arrival date"
                        " (ex. ?arrival_date=2025-09-07)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CrewListSerializer
        return CrewSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        position = self.request.query_params.get("position")

        if position:
            queryset = queryset.filter(position__name__icontains=position)

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("position")
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "position",
                type=str,
                description="Filter by crew position (ex. ?position=pilot)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_queryset(self):
        queryset = self.queryset

        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")

        if source:
            queryset = (queryset.filter
                        (flight__route__source__name__icontains=source)
                        )

        if destination:
            queryset = queryset.filter(
                flight__route__destination__name__icontains=destination
            )

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related(
                "flight__airplane",
                "flight__airplane__airplane_type",
                "flight__route__destination__city__country",
                "flight__route__source__city__country",
                "order__user"
            ).prefetch_related(
                "flight__crews__position"
            )
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "source",
                type=str,
                description=(
                        "Filter flights departing from this city"
                        " (ex. ?source=Kyiv)"
                ),
            ),
            OpenApiParameter(
                "destination",
                type=str,
                description=(
                        "Filter flights arriving to this city"
                        " (ex. ?destination=Lviv)"
                )
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_staff:
            queryset = queryset
        else:
            queryset = queryset.filter(user=self.request.user)
        ticket_queryset = Ticket.objects.select_related(
            "flight__airplane",
            "flight__route__source__city__country",
            "flight__route__destination__city__country",
        )
        queryset = queryset.prefetch_related(
            Prefetch("tickets", queryset=ticket_queryset),
        ).select_related("user")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AirplaneListSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("airplane_type")
        return queryset

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=(IsAdminUser,),
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

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
