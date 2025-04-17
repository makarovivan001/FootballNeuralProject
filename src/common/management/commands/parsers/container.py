from dependency_injector import containers, providers

from .get_clubs import ClubsParser


class Container(containers.DeclarativeContainer):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    x_mas = "eyJib2R5Ijp7InVybCI6Ii9hcGkvcGxheWVyRGF0YT9pZD0xMDI2NTEzIiwiY29kZSI6MTc0MzE2Mjc3MDg1OCwiZm9vIjoicHJvZHVjdGlvbjo0MmVlZWU2ZWUzZTM2Y2E0ODI2YTEzOTJhYjMxYTg4OTVjM2M4NzRiLXVuZGVmaW5lZCJ9LCJzaWduYXR1cmUiOiIzNDZFMTNGNjU2Q0MyRDUzMUJFMURCQTQ4QTExN0I5MyJ"
    get_clubs: ClubsParser =  providers.Factory(
        ClubsParser,
        "https://www.fotmob.com/api/leagues?id=63&ccode3=RUS&season={season}",
        "common/management/commands/parsers/",
        user_agent,
        x_mas
    )


parser_container = Container()