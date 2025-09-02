import tempfile
import uuid
from datetime import datetime

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import F, Count
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from core.models import AirplaneType, Airplane, Country, City, Airport, Route, Flight, Crew, Position, Ticket, Order
from core.serializers import FlightListSerializer, FlightRetrieveSerializer, CrewListSerializer, CrewSerializer, \
    PositionSerializer, TicketSerializer, OrderSerializer, AirplaneListSerializer, AirplaneTypeSerializer, \
    RouteListSerializer


def sample_airplane_type(**params) -> AirplaneType:
    name = params.get("name", f"Boeing-{uuid.uuid4()}")
    airplane_type, _ = AirplaneType.objects.get_or_create(name=name)
    return airplane_type


def sample_route(
        distance=500,
        source_city_name="Kyiv",
        dest_city_name="Warsaw",
        **params
) -> Route:
    source_country, _ = Country.objects.get_or_create(name="Ukraine")
    source_city, _ = City.objects.get_or_create(name=source_city_name, country=source_country)
    source_airport, _ = Airport.objects.get_or_create(name=f"{source_city_name} Airport", city=source_city)

    dest_country, _ = Country.objects.get_or_create(name="Poland")
    dest_city, _ = City.objects.get_or_create(name=dest_city_name, country=dest_country)
    dest_airport, _ = Airport.objects.get_or_create(name=f"{dest_city_name} Airport", city=dest_city)

    defaults = {
        "source": source_airport,
        "destination": dest_airport,
        "distance": distance
    }

    defaults.update(params)

    route, _ = Route.objects.get_or_create(
        source=defaults["source"],
        destination=defaults["destination"],
        defaults={"distance": defaults["distance"]}
    )
    return route


def sample_crews(**params) -> Crew:
    position, _ = Position.objects.get_or_create(name="Pilot")

    defaults = {
        "first_name": "test1",
        "last_name": "test11",
        "position": position,
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_flight(route_params=None, **params) -> Flight:
    airplane_type = sample_airplane_type()
    airplane = Airplane.objects.create(
        name=f"Boeing-{uuid.uuid4()}",
        rows=20,
        seats_in_row=6,
        airplane_type=airplane_type,
    )

    if route_params is None:
        route_params = {}

    route = sample_route(**route_params)
    crew = sample_crews()

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": datetime(2025, 12, 1, 7, 0),
        "arrival_time": datetime(2025, 12, 2, 8, 0),
    }
    defaults.update(params)
    flight = Flight.objects.create(**defaults)
    flight.crews.add(crew)
    return flight


def sample_airplane(**params) -> Airplane:
    airplane_type = sample_airplane_type()
    defaults = {
        "name":f"Boeing-{uuid.uuid4()}",
        "rows":20,
        "seats_in_row":6,
        "airplane_type":airplane_type,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def get_temporary_image():
    image = Image.new('RGB', (100, 100), color='red')
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    image.save(temp_file, format='JPEG')
    temp_file.seek(0)
    return temp_file


FLIGHT_LIST_URL = reverse("core:flight-list")
CREW_LIST_URL = reverse("core:crew-list")
POSITION_LIST_URL = reverse("core:position-list")
TICKET_LIST_URL = reverse("core:ticket-list")
ORDER_LIST_URL = reverse("core:order-list")
AIRPLANE_LIST_URL = reverse("core:airplane-list")
AIRPLANE_TYPE_LIST_URL = reverse("core:airplanetype-list")
ROUTE_LIST_URL = reverse("core:route-list")


def flight_detail_url(flight_id):
    return reverse("core:flight-detail", args=[flight_id])


def airplane_upload_url(airplane_id):
    return reverse("core:airplane-upload-image", args=[airplane_id])


def airplane_detail_url(airplane_id):
    return reverse("core:airplane-detail", args=[airplane_id])


def airplane_type_detail_url(airplane_type_id):
    return reverse("core:airplanetype-detail", args=[airplane_type_id])


def route_detail_url(route_id):
    return reverse("core:route-detail", args=[route_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_flight_list_auth_required(self):
        res = self.client.get(FLIGHT_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_flight_retrieve_auth_required(self):
        flight = sample_flight()
        res = self.client.get(flight_detail_url(flight.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_flight_list(self):
        sample_flight()

        res = self.client.get(FLIGHT_LIST_URL)
        flights = Flight.objects.annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True),
        )
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_flights_list_by_departure_city(self):
        flight_1 = sample_flight(route_params={"source_city_name": "Kyiv", "dest_city_name": "London"})
        flight_2 = sample_flight(route_params={"source_city_name": "Lviv", "dest_city_name": "Berlin"})
        res = self.client.get(
            FLIGHT_LIST_URL,
            data={
                "departure_city": "Kyiv"
            }
        )
        serializer_kyiv = FlightListSerializer(Flight.objects.filter(id=flight_1.id).annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True)
        ),
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer_kyiv.data)

    def test_filter_flights_list_by_arrival_city(self):
        flight_1 = sample_flight(route_params={"source_city_name": "London", "dest_city_name": "Kyiv"})
        flight_2 = sample_flight(route_params={"source_city_name": "Lviv", "dest_city_name": "Berlin"})
        res = self.client.get(
            FLIGHT_LIST_URL,
            data={
                "arrival_city": "Kyiv"
            }
        )
        serializer_kyiv = FlightListSerializer(Flight.objects.filter(id=flight_1.id).annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True)
        ),
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer_kyiv.data)

    def test_filter_flights_list_by_departure_time(self):
        flight_1 = sample_flight(departure_time=datetime(2020, 12, 1, 7, 0))
        flight_2 = sample_flight(departure_time=datetime(2023, 5, 1, 7, 0))
        flight_3 = sample_flight(departure_time=datetime(2025, 3, 1, 7, 0))

        res = self.client.get(
            FLIGHT_LIST_URL,
            data={
                "departure_date": flight_1.departure_time.date().isoformat()
            }
        )
        serializer = FlightListSerializer(
            Flight.objects.filter(departure_time__date=flight_1.departure_time.date()).annotate(
                tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
                crew_count=Count("crews", distinct=True)
            ),
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_flights_list_by_arrival_time(self):
        flight_1 = sample_flight(arrival_time=datetime(2020, 12, 1, 7, 0))
        flight_2 = sample_flight(arrival_time=datetime(2023, 5, 1, 7, 0))
        flight_3 = sample_flight(arrival_time=datetime(2025, 3, 1, 7, 0))

        res = self.client.get(
            FLIGHT_LIST_URL,
            data={
                "arrival_date": flight_1.arrival_time.date().isoformat()
            }
        )
        serializer = FlightListSerializer(
            Flight.objects.filter(arrival_time__date=flight_1.arrival_time.date()).annotate(
                tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
                crew_count=Count("crews", distinct=True)
            ),
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_flight_list_forbidden(self):
        flight = sample_flight()
        payload = FlightListSerializer(flight).data
        res = self.client.post(FLIGHT_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_retrieve(self):
        flight = sample_flight()

        res = self.client.get(flight_detail_url(flight.id))
        flights = Flight.objects.annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True),
        )
        flight_obj = Flight.objects.get(id=flight.id)
        serializer = FlightRetrieveSerializer(flight_obj)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_retrieve_forbidden(self):
        flight = sample_flight()
        payload = FlightRetrieveSerializer(flight).data
        res = self.client.post(flight_detail_url(flight.id), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_retrieve_not_found(self):
        fake_id = 999
        res = self.client.get(flight_detail_url(fake_id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class UnauthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_crew_auth_required(self):
        res = self.client.get(CREW_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_crew(self):
        crew_1 = sample_crews()
        crew_2 = sample_crews()
        crews = [crew_1, crew_2]

        res = self.client.get(CREW_LIST_URL)
        serializer = CrewListSerializer(crews, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_crew_by_position(self):
        crew_1 = sample_crews()
        crew_2 = sample_crews()
        res = self.client.get(
            CREW_LIST_URL,
            data={
                "position": "pilot"
            }
        )
        crews = Crew.objects.filter(position__name__icontains="pilot")
        serializer = CrewListSerializer(crews, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_crew_forbidden(self):
        crew = sample_crews()
        payload = CrewListSerializer(crew).data
        res = self.client.post(CREW_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class UnauthenticatedPositionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_position_auth_required(self):
        res = self.client.get(POSITION_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPositionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_position(self):
        position_1 = Position.objects.create(name="test1")
        position_2 = Position.objects.create(name="test2")
        positions = [position_1, position_2]
        res = self.client.get(POSITION_LIST_URL)
        serializer = PositionSerializer(positions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_position_forbidden(self):
        position = Position.objects.create(name="test")
        payload = PositionSerializer(position).data
        res = self.client.post(POSITION_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class UnauthenticatedTicketApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_ticket_auth_required(self):
        res = self.client.get(POSITION_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTicketApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_ticket(self):
        order = Order.objects.create(user=self.user)
        ticket_1 = Ticket.objects.create(
            row = 1,
            seat = 1,
            flight = sample_flight(),
            order=order
        )
        ticket_2 = Ticket.objects.create(
            row = 2,
            seat = 2,
            flight = sample_flight(),
            order=order,
        )
        tickets = [ticket_1, ticket_2]
        res = self.client.get(TICKET_LIST_URL)
        serializer = TicketSerializer(tickets, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_ticket_by_source(self):
        order = Order.objects.create(user=self.user)
        flight_1 = sample_flight(route_params={"source_city_name": "Kyiv", "dest_city_name": "London"})
        flight_2 = sample_flight(route_params={"source_city_name": "Lviv", "dest_city_name": "Berlin"})

        ticket_1 = Ticket.objects.create(
            row = 1,
            seat = 1,
            flight = flight_1,
            order = order
        )
        Ticket.objects.create(
            row = 2,
            seat = 2,
            flight = flight_2,
            order = order
        )

        res = self.client.get(
            TICKET_LIST_URL,
            data={
                "source": "Kyiv"
            }
        )
        serializer = TicketSerializer([ticket_1], many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_ticket_by_destination(self):
        order = Order.objects.create(user=self.user)
        flight_1 = sample_flight(route_params={"source_city_name": "Kyiv", "dest_city_name": "London"})
        flight_2 = sample_flight(route_params={"source_city_name": "Lviv", "dest_city_name": "Berlin"})

        ticket_1 = Ticket.objects.create(
            row=1,
            seat=1,
            flight=flight_1,
            order=order
        )
        Ticket.objects.create(
            row=2,
            seat=2,
            flight=flight_2,
            order=order
        )

        res = self.client.get(
            TICKET_LIST_URL,
            data={
                "destination": "London"
            }
        )
        serializer = TicketSerializer([ticket_1], many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_ticket_forbidden(self):
        order = Order.objects.create(user=self.user)
        flight_1 = sample_flight()
        ticket = Ticket.objects.create(
            row = 1,
            seat = 1,
            flight = flight_1,
            order=order
        )

        payload = TicketSerializer(ticket).data
        res = self.client.post(TICKET_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_order_auth_required(self):
        res = self.client.get(ORDER_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_order(self):
        order_1= Order.objects.create(user=self.user)
        order_2 = Order.objects.create(user=self.user)
        orders = [order_1, order_2]

        res = self.client.get(ORDER_LIST_URL)
        serializer = OrderSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_order_create(self):
        flight = sample_flight()
        payload = {
            "tickets": [{
                "flight": flight.id,
                "seat": 1,
                "row": 1,
            }]
        }

        res = self.client.post(ORDER_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_order_validate_value(self):
        flight = sample_flight()
        payload = {
            "tickets": [{
                "flight": flight.id,
                "seat": 10000,
                "row": 1,
            }]
        }

        res = self.client.post(ORDER_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class UnauthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_airplane_auth_required(self):
        res = self.client.get(AIRPLANE_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_airplane_upload_image_unauthorized(self):
        airplane_type = AirplaneType.objects.create(name="Airplane")
        airplane = Airplane.objects.create(
            name="Airplane1",
            rows=1,
            seats_in_row=1,
            airplane_type=airplane_type
        )
        res = self.client.post(airplane_upload_url(airplane.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)



class AuthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_airplane_list(self):
        airplane_1 = sample_airplane()
        airplane_2 = sample_airplane()
        airplanes = [airplane_1, airplane_2]

        res = self.client.get(AIRPLANE_LIST_URL)
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type, _ = AirplaneType.objects.get_or_create(name="Boeing 737")
        payload = {
            "name": "Test plane",
            "rows": 10,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_retrieve(self):
        airplane = sample_airplane()

        res = self.client.get(airplane_detail_url(airplane.id))
        serializer = AirplaneListSerializer(airplane)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_airplane_user_upload_image(self):
        airplane = sample_airplane()

        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'someimagecontent',
            content_type='image/jpeg'
        )

        res = self.client.post(
            airplane_upload_url(airplane.id),
            {"image": image},
            format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_staff_upload_image(self):
        airplane = sample_airplane()
        self.user.is_staff = True
        self.user.save()

        image = get_temporary_image()

        res = self.client.post(
            airplane_upload_url(airplane.id),
            {"image": image},
            format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airplane.refresh_from_db()
        self.assertTrue(bool(airplane.image))


class UnauthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_airplane_type_auth_required(self):
        res = self.client.get(AIRPLANE_TYPE_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_airplane_type_list(self):
        airplane_type_1 = sample_airplane_type()
        airplane_type_2 = sample_airplane_type()
        airplanes_types = [airplane_type_1, airplane_type_2]

        res = self.client.get(AIRPLANE_TYPE_LIST_URL)
        serializer = AirplaneTypeSerializer(airplanes_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_airplane_type_forbidden(self):
        payload = {
            "name": "Test type"
        }
        res = self.client.post(AIRPLANE_TYPE_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_type_retrieve(self):
        airplane = sample_airplane_type()

        res = self.client.get(airplane_type_detail_url(airplane.id))
        serializer = AirplaneTypeSerializer(airplane)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class UnauthenticatedRouterApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_route_list_auth_required(self):
        res = self.client.get(ROUTE_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_route_retrieve_auth_required(self):
        route = sample_route()
        res = self.client.get(route_detail_url(route.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_route_list(self):
        route_1 = sample_route(source_city_name="Kyiv", dest_city_name="Warsaw")
        route_2 = sample_route(source_city_name="Lviv", dest_city_name="Berlin")
        routes = [route_1, route_2]

        res = self.client.get(ROUTE_LIST_URL)
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_route_forbidden(self):
        country = Country.objects.create(name="test")
        city = City.objects.create(name="Warsaw", country=country)
        airport = Airport.objects.create(name="testairport", city=city)
        source = airport
        destination = airport
        payload = {
            "source": source,
            "destination": destination,
            "distance": 500
        }
        res = self.client.post(ROUTE_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_route_retrieve(self):
        route = sample_route()

        res = self.client.get(route_detail_url(route.id))
        serializer = RouteListSerializer(route)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)