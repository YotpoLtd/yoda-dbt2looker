from typing import Dict, List, Optional, Any

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pydantic import Field, field_validator, BaseModel, ValidationError, model_validator

from yoda_dbt2looker.models import (
    DbtNode,
    DbtModelColumn,
    ModelIntegrationConfigMetadata,
    DbtManifestMetadata
)


class DbtModelMeta(BaseModel):
    primary_key: Optional[str] = Field(None, alias="primary-key")
    integration_config: Optional[ModelIntegrationConfigMetadata] = None


class DbtModelConfig(BaseModel):
    tags: Optional[List[str]] = None


class DbtModel(DbtNode):
    resource_type: Literal["model"]
    relation_name: str
    db_schema: str = Field(..., alias="schema")
    name: str
    description: str
    columns: Dict[str, DbtModelColumn]
    tags: List[str]
    meta: DbtModelMeta
    config: DbtModelConfig

    @field_validator("columns")
    def case_insensitive_column_names(cls, v: Dict[str, DbtModelColumn]):
        return {
            name.lower(): column.copy(update={"name": column.name.lower()})
            for name, column in v.items()
        }


class DbtManifest(BaseModel):
    nodes: Dict[str, Any]
    metadata: DbtManifestMetadata

    @model_validator(mode="before")
    def validate_nodes_and_exposures(cls, values):
        nodes = values.get('nodes', {})
        # Validate 'nodes' field
        validated_nodes = {}
        for key, value in nodes.items():
            try:
                validated_nodes[key] = DbtModel(**value)
            except ValidationError as e:
                validated_nodes[key] = DbtNode(**value)
        values['nodes'] = validated_nodes
        return values
