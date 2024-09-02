from enum import Enum
from typing import Union, Dict, List, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pydantic import BaseModel, Field, PydanticValueError, validator


# dbt2looker utility types
class UnsupportedDbtAdapterError(PydanticValueError):
    code = "unsupported_dbt_adapter"
    msg_template = "{wrong_value} is not a supported dbt adapter"


class SupportedDbtAdapters(str, Enum):
    bigquery = "bigquery"
    postgres = "postgres"
    redshift = "redshift"
    snowflake = "snowflake"
    spark = "spark"


# Lookml types
class LookerAggregateMeasures(str, Enum):
    average = "average"
    average_distinct = "average_distinct"
    count = "count"
    count_distinct = "count_distinct"
    list = "list"
    max = "max"
    median = "median"
    median_distinct = "median_distinct"
    min = "min"
    # percentile = 'percentile'
    # percentile_distinct = 'percentile_distinct'
    sum = "sum"
    sum_distinct = "sum_distinct"


class LookerExposureMeasures(str, Enum):
    number = "number"
    date = "date"
    yesno = "yesno"
    string = "string"
    average = "average"
    average_distinct = "average_distinct"
    count = "count"
    count_distinct = "count_distinct"
    list = "list"
    max = "max"
    median = "median"
    median_distinct = "median_distinct"
    min = "min"
    percentile = "percentile"
    percentile_distinct = "percentile_distinct"
    sum = "sum"
    sum_distinct = "sum_distinct"


class LookerCustomDimensions(str, Enum):
    BIN = "bin"
    DATE = "date"
    DATE_TIME = "date_time"
    DISTANCE = "distance"
    LOCATION = "location"
    NUMBER = "number"
    STRING = "string"
    TIER = "tier"
    YESNO = "yesno"
    ZIPCODE = "zipcode"


class LookerParameters(str, Enum):
    DATE = "date"
    DATE_TIME = "date_time"
    NUMBER = "number"
    STRING = "string"
    UNQUOTED = "unquoted"
    YESNO = "yesno"


class DimensionGroupTimeType(str, Enum):
    TIME = "time"


class DimensionGroupDurationType(str, Enum):
    DURATION = "duration"


class LookerFilters(str, Enum):
    DATE = "date"
    DATE_TIME = "date_time"
    NUMBER = "number"
    STRING = "string"
    YESNO = "yesno"


class LookerJoinType(str, Enum):
    left_outer = "left_outer"
    full_outer = "full_outer"
    inner = "inner"
    cross = "cross"


class LookerJoinRelationship(str, Enum):
    many_to_one = "many_to_one"
    many_to_many = "many_to_many"
    one_to_many = "one_to_many"
    one_to_one = "one_to_one"


class LookerValueFormatName(str, Enum):
    decimal_0 = "decimal_0"
    decimal_1 = "decimal_1"
    decimal_2 = "decimal_2"
    decimal_3 = "decimal_3"
    decimal_4 = "decimal_4"
    usd_0 = "usd_0"
    usd = "usd"
    gbp_0 = "gbp_0"
    gbp = "gbp"
    eur_0 = "eur_0"
    eur = "eur"
    id = "id"
    percent_0 = "percent_0"
    percent_1 = "percent_1"
    percent_2 = "percent_2"
    percent_3 = "percent_3"
    percent_4 = "percent_4"


class Dbt2LookerMeasure(BaseModel):
    type: LookerAggregateMeasures
    filters: Optional[List[Dict[str, str]]] = []
    description: Optional[str]
    sql: Optional[str]
    value_format_name: Optional[LookerValueFormatName]
    label: Optional[str] = None

    @validator("filters")
    def filters_are_singular_dicts(cls, v: List[Dict[str, str]]):
        if v is not None:
            for f in v:
                if len(f) != 1:
                    raise ValueError(
                        "Multiple filter names provided for a single filter in measure block"
                    )
        return v


class Dbt2LookerDimension(BaseModel):
    enabled: Optional[bool] = True
    name: Optional[str]
    sql: Optional[str]
    description: Optional[str]
    value_format_name: Optional[LookerValueFormatName]


class Dbt2InnerLookerMeta(BaseModel):
    measures: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    measure: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    metrics: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    metric: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    dimension: Optional[Dbt2LookerDimension] = Dbt2LookerDimension()


class Dbt2LookerMeta(BaseModel):
    looker: Optional[Dbt2InnerLookerMeta] = Dbt2InnerLookerMeta()
    measures: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    measure: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    metrics: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    metric: Optional[Dict[str, Dbt2LookerMeasure]] = {}
    dimension: Optional[Dbt2LookerDimension] = Dbt2LookerDimension()


# Looker file types
class LookViewFile(BaseModel):
    filename: str
    contents: str


class LookModelFile(BaseModel):
    filename: str
    contents: str


# dbt config types
class DbtProjectConfig(BaseModel):
    name: str


class DbtModelColumnMeta(Dbt2LookerMeta):
    pass


class DbtModelColumn(BaseModel):
    name: str
    description: str
    data_type: Optional[str]
    meta: DbtModelColumnMeta


class DbtNode(BaseModel):
    unique_id: str
    resource_type: str


class Dbt2LookerExploreJoin(BaseModel):
    join: str
    type: Optional[LookerJoinType] = LookerJoinType.left_outer
    relationship: Optional[LookerJoinRelationship] = LookerJoinRelationship.many_to_one
    sql_on: str


class Dbt2LookerExploreMeasure(BaseModel):
    name: str
    model: str
    type: LookerExposureMeasures
    sql: str
    filters: Optional[List[Dict[str, str]]] = None
    description: Optional[str] = ""
    label: Optional[str] = None


class Dbt2LookerExploreDimension(BaseModel):
    name: str
    model: str
    type: LookerCustomDimensions
    sql: str
    primary_key: bool = False
    hidden: Optional[str] = None
    description: Optional[str] = ""
    label: Optional[str] = None


class Dbt2LookerExploreParameter(BaseModel):
    name: str
    model: str
    type: LookerParameters
    label: Optional[str] = None
    allowed_value: Optional[List[str]] = None
    description: Optional[str] = ""


class Dbt2LookerExploreFilter(BaseModel):
    name: str
    model: str
    type: LookerFilters
    label: Optional[str] = None
    sql: Optional[str] = None
    description: Optional[str] = ""


class Dbt2LookerExploreDimensionGroupDuration(BaseModel):
    name: str
    model: str
    type: DimensionGroupDurationType
    sql_start: str
    sql_end: str
    intervals: Optional[List[str]] = None
    datatype: Optional[str] = None
    description: Optional[str] = ""


class Dbt2LookerModelLabels(BaseModel):
    model: str
    model_label: str
    columns_labels: Dict[str, str]


class Dbt2MetaLookerModelMeta(BaseModel):
    joins: Optional[List[Dbt2LookerExploreJoin]] = []
    main_model: str
    connection: str
    sql_always_where: Optional[str] = None
    measures: Optional[List[Dbt2LookerExploreMeasure]] = []
    dimensions: Optional[List[Dbt2LookerExploreDimension]] = []
    dimension_groups: Optional[List[Dbt2LookerExploreDimensionGroupDuration]] = []
    parameters: Optional[List[Dbt2LookerExploreParameter]] = []
    filters: Optional[List[Dbt2LookerExploreFilter]] = []
    model_labels: Optional[List[Dbt2LookerModelLabels]]


class Dbt2LookerModelMeta(BaseModel):
    looker: Optional[Dbt2MetaLookerModelMeta]
    joins: Optional[List[Dbt2LookerExploreJoin]] = []


class SnowflakeProperties(BaseModel):
    table: str
    sf_schema: str = Field(None, alias="schema")


class SnowflakeConfiguration(BaseModel):
    properties: SnowflakeProperties = None


class ModelIntegrationConfigMetadata(BaseModel):
    snowflake: Optional[SnowflakeConfiguration] = None


class DbtModelMeta(Dbt2LookerModelMeta):
    primary_key: Optional[str] = Field(None, alias="primary-key")
    integration_config: Optional[ModelIntegrationConfigMetadata] = None


class DbtModel(DbtNode):
    resource_type: Literal["model"]
    relation_name: str
    db_schema: str = Field(..., alias="schema")
    name: str
    description: str
    columns: Dict[str, DbtModelColumn]
    tags: List[str]
    meta: DbtModelMeta
    create_explorer: bool = True
    measures_exposure: Optional[List[Dbt2LookerExploreMeasure]] = []
    calculated_dimension: Optional[List[Dbt2LookerExploreDimension]] = []
    dimension_groups_exposure: Optional[
        List[Dbt2LookerExploreDimensionGroupDuration]
    ] = []
    parameters_exposure: Optional[List[Dbt2LookerExploreParameter]] = []
    filters_exposure: Optional[List[Dbt2LookerExploreFilter]] = []
    model_labels: Optional[Dbt2LookerModelLabels]

    @validator("columns")
    def case_insensitive_column_names(cls, v: Dict[str, DbtModelColumn]):
        return {
            name.lower(): column.copy(update={"name": column.name.lower()})
            for name, column in v.items()
        }


class DbtExposureDependsOn(BaseModel):
    macros: List[str]
    nodes: List[str]


class DbtExposure(DbtNode):
    resource_type: Literal["exposure"]
    name: str
    description: str
    tags: List[str]
    depends_on: DbtExposureDependsOn
    meta: DbtModelMeta
    original_file_path: str
    path: str


class DbtManifestMetadata(BaseModel):
    adapter_type: str

    @validator("adapter_type")
    def adapter_must_be_supported(cls, v):
        try:
            SupportedDbtAdapters(v)
        except ValueError:
            raise UnsupportedDbtAdapterError(wrong_value=v)
        return v


class DbtManifest(BaseModel):
    nodes: Dict[str, Union[DbtModel, DbtNode]]
    exposures: Dict[str, Union[DbtExposure, DbtNode]]
    metadata: DbtManifestMetadata