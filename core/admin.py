from django.contrib import admin

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
    Country,
)

admin.site.register(Flight)
admin.site.register(Crew)
admin.site.register(Position)
admin.site.register(Ticket)
admin.site.register(Order)
admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Route)
admin.site.register(Airport)
admin.site.register(City)
admin.site.register(Country)
