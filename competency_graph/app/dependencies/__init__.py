from dependency_injector import containers, providers
from SPARQLWrapper import SPARQLWrapper

from dependencies.config import Config
from dependencies.graphdb import create_graphdb_client
from dependencies.postgres import create_db_pool


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["api.v1", "dao"],
    )

    config: providers.Provider[Config] = providers.Singleton(Config)

    # request_context: providers.Provider[RequestContext] = providers.Singleton(RequestContext)

    graphdb_client: providers.Provider[SPARQLWrapper] = providers.Resource(
        create_graphdb_client,
        config=config
    )

    db_pool = providers.Resource(
        create_db_pool,
        config=config
    )

