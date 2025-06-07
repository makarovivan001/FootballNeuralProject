from dependency_injector import containers, providers

from domain.interfaces.repositories.season.main import ISeasonRepository
from infrastructure.repositories.season.main import SeasonRepository


class Container(containers.DeclarativeContainer):
     season_repository: ISeasonRepository = providers.Factory(
         SeasonRepository
     )



container = Container()