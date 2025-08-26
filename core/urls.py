from django.urls import path, include
from rest_framework import routers

from core.views import (
    FlightViewSet,
    CrewViewSet,
    PositionViewSet,
    TicketViewSet,
    OrderViewSet,
    RouteViewSet,
    AirportViewSet,
    CityViewSet,
    CountryViewSet,
    AirplaneViewSet,
    AirplaneTypeViewSet
)

app_name = "core"


router = routers.DefaultRouter()

router.register("flights", FlightViewSet)
router.register("crews", CrewViewSet)
router.register("positions", PositionViewSet)
router.register("tickets", TicketViewSet)
router.register("orders", OrderViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("airplane-types", AirplaneTypeViewSet)
router.register("routes", RouteViewSet)
router.register("airports", AirportViewSet)
router.register("cities", CityViewSet)
router.register("countries", CountryViewSet)

urlpatterns = [
    path("", include(router.urls))
]
