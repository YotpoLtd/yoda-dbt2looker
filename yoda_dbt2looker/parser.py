import logging
import json
import jsonschema
import importlib.resources
from typing import Dict, Optional, List, Union
from functools import reduce

from pydantic.main import BaseModel

from .generator import _extract_all_refs
from . import models


def validate_manifest(raw_manifest: dict):
    with importlib.resources.open_text(
        "yoda_dbt2looker.dbt_json_schemas", "manifest_dbt2looker.json"
    ) as f:
        schema = json.load(f)
    v = jsonschema.Draft7Validator(schema)
    hasError = False
    for error in v.iter_errors(raw_manifest):
        raise_error_context(error)
        hasError = True
    if hasError:
        raise ValueError("Failed to parse dbt manifest.json")
    return True


def raise_error_context(error: jsonschema.ValidationError, offset=""):
    for error in sorted(error.context, key=lambda e: e.schema_path):
        raise_error_context(error, offset=offset + "  ")
    path = ".".join([str(p) for p in error.absolute_path])
    logging.error(f"{offset}Error in manifest at {path}: {error.message}")


def parse_dbt_project_config(raw_config: dict):
    return models.DbtProjectConfig(**raw_config)


def parse_adapter_type(raw_manifest: dict):
    manifest = models.DbtManifest(**raw_manifest)
    return manifest.metadata.adapter_type


def tags_match(query_tag: str, model: models.DbtModel) -> bool:
    try:
        return query_tag in model.tags
    except AttributeError:
        return False
    except ValueError:
        # Is the tag just a string?
        return query_tag == model.tags


def parse_models(raw_manifest: dict, tag=None) -> List[models.DbtModel]:
    manifest = models.DbtManifest(**raw_manifest)
    all_models: List[models.DbtModel] = [
        node for node in manifest.nodes.values() if node.resource_type == "model"
    ]

    # Empty model files have many missing parameters
    for model in all_models:
        if not hasattr(model, "name"):
            logging.error(
                'Cannot parse model with id: "%s" - is the model file empty?',
                model.unique_id,
            )
            raise SystemExit("Failed")

    if tag is None:
        return all_models
    return [model for model in all_models if tags_match(tag, model)]


def parse_exposures(raw_manifest: dict, tag=None) -> List[models.DbtExposure]:
    manifest = models.DbtManifest(**raw_manifest)
    # Empty model files have many missing parameters
    all_exposures = manifest.exposures.values()
    for exposure in all_exposures:
        if not hasattr(exposure, "name"):
            logging.error(
                'Cannot parse exposure with id: "%s" - is the exposure file empty?',
                exposure.unique_id,
            )
            logging.error(exposure.resource_type)
            raise SystemExit("Failed")

    if tag is None:
        return all_exposures
    return [exposure for exposure in all_exposures if tags_match(tag, exposure)]


def check_models_for_missing_column_types(dbt_typed_models: List[models.DbtModel]):
    for model in dbt_typed_models:
        if all([col.data_type is None for col in model.columns.values()]):
            logging.debug(
                "Model %s has no typed columns, no dimensions will be generated. %s",
                model.unique_id,
                model,
            )


def parse_typed_models(
    raw_manifest: dict,
    dbt_project_name: str,
    tag: Optional[str] = None,
):
    dbt_models = parse_models(raw_manifest, tag=tag)
    manifest = models.DbtManifest(**raw_manifest)
    typed_dbt_exposures: List[models.DbtExposure] = parse_exposures(
        raw_manifest, tag=tag
    )
    exposure_nodes = []

    exposure_model_views = set()
    model_to_measure = {}
    calculated_dimension = {}
    dimension_groups = {}
    parameters = {}
    filters = {}
    models_labels = {}
    for exposure in typed_dbt_exposures:
        ref_model = _extract_all_refs(exposure.meta.looker.main_model)
        if not ref_model:
            logging.error(
                f"Exposure main_model {exposure.meta.looker.main_model} should be ref('model_name')"
            )
            raise Exception(
                f"Exposure main_model {exposure.meta.looker.main_model} should be ref('model_name')"
            )
        exposure_model_views.add(ref_model[0])

        if exposure.meta.looker.joins:
            for join in exposure.meta.looker.joins:
                if _extract_all_refs(join.sql_on) == None:
                    logging.error(
                        f"Exposure join.sql_on {join.sql_on} should be ref('model_name')"
                    )
                    raise Exception(
                        f"Exposure join.sql_on {join.sql_on} should be ref('model_name')"
                    )

            for item in reduce(
                list.__add__,
                [_extract_all_refs(join.sql_on) for join in exposure.meta.looker.joins],
            ):
                exposure_model_views.add(item)
        _extract_measures_models(exposure_model_views, model_to_measure, exposure)
        _extract_exposure_models(
            exposure_model_views, calculated_dimension, exposure.meta.looker.dimensions
        )
        _extract_exposure_models(
            exposure_model_views, parameters, exposure.meta.looker.parameters
        )
        _extract_exposure_models(
            exposure_model_views, filters, exposure.meta.looker.filters
        )
        _extract_exposure_models(
            exposure_model_views,
            dimension_groups,
            exposure.meta.looker.dimension_groups,
        )
        _extract_exposure_models(
            exposure_model_views,
            models_labels,
            exposure.meta.looker.model_labels,
        )

    for model in exposure_model_views:
        model_loopup = f"model.{dbt_project_name}.{model}"
        model_node = manifest.nodes.get(model_loopup)
        if not model_node:
            logging.error(f"Exposure join.sql_on model {model_loopup} missing")
            raise Exception(f"Exposure join.sql_on model {model_loopup} missing")
        model_node.create_explorer = False
        if model in model_to_measure:
            model_node.measures_exposure = model_to_measure[model]
        if model in calculated_dimension:
            model_node.calculated_dimension = calculated_dimension[model]
        if model in dimension_groups:
            model_node.dimension_groups_exposure = dimension_groups[model]
        if model in parameters:
            model_node.parameters_exposure = parameters[model]
        if model in filters:
            model_node.filters_exposure = filters[model]
        _assign_model_labels(models_labels, model, model_node)
        exposure_nodes.append(model_node)

    adapter_type = parse_adapter_type(raw_manifest)
    dbt_models = dbt_models + exposure_nodes
    logging.debug("Parsed %d models from manifest.json", len(dbt_models))
    for model in dbt_models:
        logging.debug(
            "Model %s has %d columns with %d measures",
            model.name,
            len(model.columns),
            reduce(
                lambda acc, col: acc
                + len(col.meta.measures)
                + len(col.meta.measure)
                + len(col.meta.metrics)
                + len(col.meta.metric),
                model.columns.values(),
                0,
            ),
        )

    logging.debug("Found %d models", len(dbt_models))
    check_models_for_missing_column_types(dbt_models)
    return dbt_models


def _assign_model_labels(models_labels, model, model_node):
    if model in models_labels:
        if len(models_labels[model]) > 1:
            logging.error(
                f"Exposure model_labels {models_labels[model]} should be a list of one element"
            )
            raise Exception(
                f"Exposure model_labels should be a list of one element for model {model}"
            )
        model_node.model_labels = models_labels[model][0]



def _extract_measures_models(
    exposure_model_views: set[str],
    model_to_measure: dict[str, list[models.Dbt2LookerExploreMeasure]],
    exposure: models.DbtExposure,
):
    if exposure.meta.looker.measures:
        for measure in exposure.meta.looker.measures:
            if not _extract_all_refs(measure.model):
                logging.error(
                    f"Exposure measure.model {measure.model} should be ref('model_name')"
                )
                raise Exception(
                    f"Exposure measure.model {measure.model} should be ref('model_name')"
                )
            if not _extract_all_refs(measure.sql):
                logging.error(
                    f"Exposure measure.sql {measure.sql} should be ref('model_name')"
                )
                raise Exception(
                    f"Exposure measure.sql {measure.sql} should be ref('model_name')"
                )
            main_measure_model = _extract_all_refs(measure.model)[0]
            exposure_model_views.add(main_measure_model)
            if not model_to_measure.get(main_measure_model):
                model_to_measure[main_measure_model] = []
            model_to_measure[main_measure_model].append(measure)
            exposure_model_views.update(_extract_all_refs(measure.sql))


def _extract_exposure_models(
    exposure_model_views: set[str],
    exposure_model: dict[str, list[BaseModel]],
    looker_exposure_objects: Optional[List[BaseModel]],
):
    if looker_exposure_objects:
        for looker_exposure_object in looker_exposure_objects:
            if not _extract_all_refs(looker_exposure_object.model):
                logging.error(
                    f"Exposure model {looker_exposure_object.model} should be ref('model_name')"
                )
                raise Exception(
                    f"Exposure model {looker_exposure_object.model} should be ref('model_name')"
                )
            main_model = _extract_all_refs(looker_exposure_object.model)[0]
            exposure_model_views.add(main_model)
            if not exposure_model.get(main_model):
                exposure_model[main_model] = []
            exposure_model[main_model].append(looker_exposure_object)