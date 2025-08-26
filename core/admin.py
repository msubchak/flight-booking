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


class AirportAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
    )


class CityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "country",
    )


class CrewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "position",
    )


class AirplaneAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "rows",
        "seats_in_row",
        "airplane_type",
    )


class TicketInLine(admin.TabularInline):
    model = Ticket
    extra = 1


class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInLine,)


admin.site.register(Flight)
admin.site.register(Crew, CrewAdmin)
admin.site.register(Position)
admin.site.register(Ticket)
admin.site.register(Order, OrderAdmin)
admin.site.register(Airplane, AirplaneAdmin)
admin.site.register(AirplaneType)
admin.site.register(Route)
admin.site.register(Airport, AirportAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Country)
